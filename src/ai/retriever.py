import os
from typing import List
from concurrent.futures import ThreadPoolExecutor
from qdrant_client import QdrantClient
from qdrant_client.http import models
from langchain_qdrant import QdrantVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document


class ParentDocumentRetriever:
    def __init__(self, client: QdrantClient, embeddings: OpenAIEmbeddings):
        self.client = client
        self.embeddings = embeddings
        self.child_collection = "cheonan_child_chunks"

        # Child vectorstore
        self.child_vectorstore = QdrantVectorStore(
            client=self.client,
            collection_name=self.child_collection,
            embedding=self.embeddings
        )

        # Parent docstore 생성 (04 노트북 방식)
        print("Parent docstore 생성 중...")
        self.parent_docstore = self._build_parent_docstore()
        print(f"Parent docstore 생성 완료: {len(self.parent_docstore)}개 페이지")

    def _build_parent_docstore(self) -> dict:
        """
        Qdrant에서 모든 child chunk를 가져와 parent_id별로 결합

        Returns:
            parent_docstore: {parent_id: Document} dict
        """
        try:
            # Qdrant에서 모든 child chunk 가져오기
            all_chunks = []
            offset = None

            while True:
                results = self.client.scroll(
                    collection_name=self.child_collection,
                    limit=100,
                    offset=offset,
                    with_payload=True,
                    with_vectors=False
                )

                points, next_offset = results

                if not points:
                    break

                for point in points:
                    all_chunks.append(Document(
                        page_content=point.payload.get("page_content", ""),
                        metadata=point.payload.get("metadata", {})
                    ))

                if next_offset is None:
                    break

                offset = next_offset

            # Parent_id별로 chunk 그룹화
            parent_groups = {}
            for chunk in all_chunks:
                parent_id = chunk.metadata.get("parent_id")
                if parent_id:
                    if parent_id not in parent_groups:
                        parent_groups[parent_id] = []
                    parent_groups[parent_id].append(chunk)

            # 각 parent의 모든 chunk를 결합하여 docstore 생성
            parent_docstore = {}
            for parent_id, chunks in parent_groups.items():
                # Chunk들을 결합
                combined_content = "\n\n".join([chunk.page_content for chunk in chunks])

                # 첫 번째 chunk의 메타데이터 사용
                first_chunk = chunks[0]
                parent_doc = Document(
                    page_content=combined_content,
                    metadata={
                        "source": first_chunk.metadata.get("source", "알 수 없음"),
                        "page": first_chunk.metadata.get("page"),
                        "parent_id": parent_id
                    }
                )
                parent_docstore[parent_id] = parent_doc

            return parent_docstore

        except Exception as e:
            print(f"Parent docstore 생성 오류: {e}")
            return {}

    def search(self, query: str, k: int = 2) -> List[Document]:
        """
        04 노트북과 동일: Child chunk 검색 → Parent docstore에서 가져오기

        Args:
            query: 검색 쿼리
            k: 반환할 parent 문서 개수

        Returns:
            Parent 문서 리스트
        """
        try:
            # 1. Child chunk 검색
            child_results = self.child_vectorstore.similarity_search(query, k=k*2)

            if not child_results:
                return []

            # 2. Parent_id 추출 (중복 제거, 순서 유지)
            parent_ids = []
            for doc in child_results:
                parent_id = doc.metadata.get("parent_id")
                if parent_id and parent_id not in parent_ids:
                    parent_ids.append(parent_id)
                    if len(parent_ids) >= k:
                        break

            # 3. Parent docstore에서 parent 문서 가져오기
            parent_docs = []
            for parent_id in parent_ids:
                if parent_id in self.parent_docstore:
                    parent_docs.append(self.parent_docstore[parent_id])

            return parent_docs

        except Exception as e:
            print(f"Parent Document Retriever 오류: {e}")
            return []


class MetadataFilteredRetriever:
    def __init__(self, client: QdrantClient, embeddings: OpenAIEmbeddings):
        self.client = client
        self.embeddings = embeddings
        self.collection_name = "cheonan_metadata"

        # Vectorstore
        self.vectorstore = QdrantVectorStore(
            client=self.client,
            collection_name=self.collection_name,
            embedding=self.embeddings
        )

    def search(self, query: str, k: int = 3, categories: List[str] = None) -> List[Document]:
        """
        메타데이터 필터링 검색

        Args:
            query: 검색 쿼리
            k: 반환할 문서 개수
            categories: 카테고리 필터 리스트 (선택사항)

        Returns:
            검색된 문서 리스트
        """
        try:
            # 카테고리 필터가 있으면 적용
            filter_conditions = None
            if categories:
                # 여러 카테고리에 대해 OR 조건 적용
                if len(categories) == 1:
                    filter_conditions = models.Filter(
                        must=[
                            models.FieldCondition(
                                key="metadata.category",
                                match=models.MatchValue(value=categories[0])
                            )
                        ]
                    )
                else:
                    # 여러 카테고리는 should (또는 OR) 조건으로 처리
                    filter_conditions = models.Filter(
                        should=[
                            models.FieldCondition(
                                key="metadata.category",
                                match=models.MatchValue(value=cat)
                            )
                            for cat in categories
                        ]
                    )

            # 검색 수행
            results = self.vectorstore.similarity_search(
                query,
                k=k,
                filter=filter_conditions
            )

            return results

        except Exception as e:
            print(f"Metadata Filtered Retriever 오류: {e}")
            return []

# =======================================
# 병렬 검색을 수행하는 VectorRetriever 클래스
# =======================================


class VectorRetriever:
    def __init__(self):
        """Qdrant 벡터 검색기 초기화"""
        # Qdrant 클라이언트 초기화
        self.client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY")
        )

        # 임베딩 모델 초기화
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-large"
        )

        # 두 retriever 초기화
        self.parent_retriever = ParentDocumentRetriever(
            self.client,
            self.embeddings
        )
        self.metadata_retriever = MetadataFilteredRetriever(
            self.client,
            self.embeddings
        )

    def search(self, query: str, k: int = 3, score_threshold: float = 0.5, categories: List[str] = None) -> list[Document]:
        """
        병렬 벡터 검색 수행

        ParentDocumentRetriever와 MetadataFilteredRetriever를
        동시에 실행하고 결과를 통합합니다.

        Args:
            query: 검색 쿼리
            k: 각 retriever당 반환할 문서 개수
            score_threshold: 최소 유사도 임계값 (미사용, 호환성 유지)
            categories: 메타데이터 필터링에 사용할 카테고리 리스트 (선택사항)

        Returns:
            검색된 문서 리스트 (중복 제거)
        """
        try:
            # 두 검색을 병렬로 실행
            with ThreadPoolExecutor(max_workers=2) as executor:
                # Parent retriever 실행
                parent_future = executor.submit(
                    self.parent_retriever.search,
                    query,
                    k=max(1, k//2)  # k의 절반
                )

                # Metadata retriever 실행 (카테고리 필터 적용)
                metadata_future = executor.submit(
                    self.metadata_retriever.search,
                    query,
                    k=k,
                    categories=categories  # 카테고리 리스트 전달
                )

                # 결과 수집
                parent_results = parent_future.result()
                metadata_results = metadata_future.result()

            # 결과 통합 (중복 제거)
            all_results = []
            seen_contents = set()

            # Parent results 추가
            for doc in parent_results:
                content_hash = hash(doc.page_content[:200])  # 앞 200자로 중복 체크
                if content_hash not in seen_contents:
                    seen_contents.add(content_hash)
                    all_results.append(doc)

            # Metadata results 추가
            for doc in metadata_results:
                content_hash = hash(doc.page_content[:200])
                if content_hash not in seen_contents:
                    seen_contents.add(content_hash)
                    all_results.append(doc)

            # 최대 k개까지만 반환
            return all_results[:k*2]  # 두 소스에서 가져오므로 2배

        except Exception as e:
            print(f"벡터 검색 오류: {e}")
            # 에러 발생 시 최소한 하나라도 시도
            try:
                return self.metadata_retriever.search(query, k=k)
            except:
                return []

    def is_relevant(self, results: list[Document], min_count: int = 1) -> bool:
        """
        검색 결과가 충분히 관련성이 있는지 확인

        Args:
            results: 검색 결과
            min_count: 최소 필요 문서 개수

        Returns:
            관련성 있는 결과가 충분한지 여부
        """
        return len(results) >= min_count


def get_retriever() -> VectorRetriever:
    """벡터 검색기 인스턴스 반환"""
    return VectorRetriever()
