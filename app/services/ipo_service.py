from typing import Optional, List
from sqlalchemy.orm import Session
from app.repositories import IPORepository, GMPRepository, SubscriptionRepository
from app.schemas.ipo import IPOResponse, IPOListResponse, IPOSummaryResponse
from app.schemas.gmp import GMPResponse, GMPHistoryListResponse
from app.schemas.subscription import SubscriptionResponse, SubscriptionHistoryListResponse
from app.models.ipo import IPOStatus, IssueType
from app.core.exceptions import IPONotFoundException

class IPOService:
    def __init__(self, db: Session):
        self.ipo_repo = IPORepository(db)
        self.gmp_repo = GMPRepository(db)
        self.sub_repo = SubscriptionRepository(db)

    def get_ipo_or_raise(self, identifier: str):
        ipo = self.ipo_repo.get_by_id_or_symbol(identifier)
        if not ipo:
            raise IPONotFoundException(identifier)
        return ipo

    def list_ipos(
        self,
        status: Optional[IPOStatus] = None,
        issue_type: Optional[IssueType] = None,
        page: int = 1,
        limit: int = 20
    ) -> IPOListResponse:
        ipos, total = self.ipo_repo.list_ipos(status=status, issue_type=issue_type, page=page, limit=limit)
        return IPOListResponse(
            total=total,
            page=page,
            limit=limit,
            ipos=[IPOResponse.model_validate(ipo) for ipo in ipos]
        )

    def list_open_ipos(self) -> List[IPOResponse]:
        ipos = self.ipo_repo.list_open()
        return [IPOResponse.model_validate(ipo) for ipo in ipos]

    def list_upcoming_ipos(self) -> List[IPOResponse]:
        ipos = self.ipo_repo.list_upcoming()
        return [IPOResponse.model_validate(ipo) for ipo in ipos]

    def get_ipo_detail(self, identifier: str) -> IPOResponse:
        ipo = self.get_ipo_or_raise(identifier)
        return IPOResponse.model_validate(ipo)

    def get_gmp_latest(self, identifier: str) -> GMPResponse:
        ipo = self.get_ipo_or_raise(identifier)
        gmp = self.gmp_repo.get_latest_gmp(ipo.id)
        if not gmp:
            raise IPONotFoundException(f"GMP for {identifier}")
        
        resp = GMPResponse.model_validate(gmp)
        if gmp.source:
            resp.source_code = gmp.source.code
        return resp

    def get_gmp_history(self, identifier: str, limit: int = 50) -> GMPHistoryListResponse:
        ipo = self.get_ipo_or_raise(identifier)
        records = self.gmp_repo.get_gmp_history(ipo.id, limit=limit)
        
        gmp_responses = []
        for r in records:
            res = GMPResponse.model_validate(r)
            if r.source:
                res.source_code = r.source.code
            gmp_responses.append(res)

        return GMPHistoryListResponse(
            ipo_id=ipo.id,
            symbol=ipo.symbol,
            count=len(gmp_responses),
            history=gmp_responses
        )

    def get_subscription_history(self, identifier: str, limit: int = 50) -> SubscriptionHistoryListResponse:
        ipo = self.get_ipo_or_raise(identifier)
        records = self.sub_repo.get_subscription_history(ipo.id, limit=limit)
        
        sub_responses = []
        for r in records:
            res = SubscriptionResponse.model_validate(r)
            if r.source:
                res.source_code = r.source.code
            sub_responses.append(res)

        latest = sub_responses[0] if sub_responses else None

        return SubscriptionHistoryListResponse(
            ipo_id=ipo.id,
            symbol=ipo.symbol,
            count=len(sub_responses),
            latest=latest,
            history=sub_responses
        )

    def get_ipo_summary(self, identifier: str) -> IPOSummaryResponse:
        ipo = self.get_ipo_or_raise(identifier)
        gmp = self.gmp_repo.get_latest_gmp(ipo.id)
        sub = self.sub_repo.get_latest_subscription(ipo.id)

        gmp_resp = None
        est_return = None
        if gmp:
            gmp_resp = GMPResponse.model_validate(gmp)
            if gmp.source:
                gmp_resp.source_code = gmp.source.code
            if gmp.gmp_percent is not None:
                est_return = float(gmp.gmp_percent)
            elif ipo.max_price and float(ipo.max_price) > 0:
                est_return = round((float(gmp.gmp_price) / float(ipo.max_price)) * 100, 2)

        sub_resp = None
        if sub:
            sub_resp = SubscriptionResponse.model_validate(sub)
            if sub.source:
                sub_resp.source_code = sub.source.code

        return IPOSummaryResponse(
            ipo=IPOResponse.model_validate(ipo),
            latest_gmp=gmp_resp,
            latest_subscription=sub_resp,
            estimated_return_percent=est_return
        )
