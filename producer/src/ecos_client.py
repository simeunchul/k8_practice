"""한국은행 ECOS OpenAPI 클라이언트.

발급: https://ecos.bok.or.kr/api  (무료, 일 호출 제한 있음)
호출 형식: https://ecos.bok.or.kr/api/StatisticSearch/{KEY}/json/kr/1/100/{통계표코드}/{주기}/{시작}/{끝}/{항목코드}
"""
import requests

ECOS_BASE = "https://ecos.bok.or.kr/api"


class EcosClient:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def fetch_statistic(
        self,
        stat_code: str,
        cycle: str,
        start: str,
        end: str,
        item_code: str = "",
    ) -> list[dict]:
        """통계표 한 건을 조회해 row 리스트로 반환한다.

        TODO(Phase 0 후반):
          - 실제 통계표 코드/항목코드 채우기 (예: 722Y001 기준금리)
          - 응답 JSON의 StatisticSearch.row 파싱
          - 에러/Rate limit 핸들링
        """
        url = (
            f"{ECOS_BASE}/StatisticSearch/{self.api_key}/json/kr/1/100/"
            f"{stat_code}/{cycle}/{start}/{end}/{item_code}"
        )
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("StatisticSearch", {}).get("row", [])
