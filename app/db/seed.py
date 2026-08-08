from datetime import datetime, date, timedelta, timezone
from sqlalchemy.orm import Session
from app.models import (
    Base,
    DataSource, SourceType,
    IPO, IssueType, IPOStatus,
    GMPHistory,
    SubscriptionHistory,
    Notification, NotificationType, NotificationStatus,
    APIRequest,
    WorkflowHealth, HealthStatus
)

def seed_db(db: Session):
    # 1. Create Data Sources
    ds_upstox = DataSource(
        code="UPSTOX_API",
        name="Upstox Developer API v2",
        source_type=SourceType.OFFICIAL,
        is_active=True,
        priority=1,
        config_metadata={"endpoint": "https://api.upstox.com/v2/ipos"}
    )
    ds_apify = DataSource(
        code="APIFY_GMP",
        name="Apify Indian IPO Tracker Gateway",
        source_type=SourceType.UNOFFICIAL_GMP,
        is_active=True,
        priority=1,
        config_metadata={"provider": "Apify", "target": "InvestorGain"}
    )
    ds_investorgain = DataSource(
        code="INVESTOR_GAIN",
        name="InvestorGain Direct Scraper",
        source_type=SourceType.UNOFFICIAL_GMP,
        is_active=True,
        priority=2,
        config_metadata={"url": "https://investorgain.com"}
    )
    ds_nse = DataSource(
        code="NSE_DIRECT",
        name="National Stock Exchange E-IPO",
        source_type=SourceType.OFFICIAL,
        is_active=True,
        priority=2,
        config_metadata={"url": "https://nseindia.com"}
    )
    ds_linkintime = DataSource(
        code="LINK_INTIME",
        name="Link Intime India Registrar",
        source_type=SourceType.REGISTRAR,
        is_active=True,
        priority=1,
        config_metadata={"url": "https://linkintime.co.in"}
    )

    db.add_all([ds_upstox, ds_apify, ds_investorgain, ds_nse, ds_linkintime])
    db.flush()

    # 2. Create IPO Master Records
    now = datetime.now(timezone.utc)
    today = date.today()

    ipo_swiggy = IPO(
        symbol="SWIGGY",
        bse_code="544280",
        company_name="Swiggy Limited",
        issue_type=IssueType.MAINBOARD,
        status=IPOStatus.OPEN,
        min_price=371.00,
        max_price=390.00,
        issue_price=390.00,
        lot_size=38,
        total_issue_size_cr=11327.43,
        fresh_issue_cr=4499.00,
        offer_for_sale_cr=6828.43,
        open_date=today - timedelta(days=1),
        close_date=today + timedelta(days=1),
        allotment_date=today + timedelta(days=4),
        listing_date=today + timedelta(days=7),
        registrar_name="Link Intime India Private Ltd",
        registrar_url="https://linkintime.co.in/initial_offer/public-issues.html",
        rhp_url="https://www.sebi.gov.in/swiggy-rhp.pdf",
        primary_source_id=ds_upstox.id
    )

    ipo_hyundai = IPO(
        symbol="HYUNDAI",
        bse_code="544275",
        company_name="Hyundai Motor India Limited",
        issue_type=IssueType.MAINBOARD,
        status=IPOStatus.LISTED,
        min_price=1860.00,
        max_price=1960.00,
        issue_price=1960.00,
        lot_size=7,
        total_issue_size_cr=27870.16,
        fresh_issue_cr=0.00,
        offer_for_sale_cr=27870.16,
        open_date=today - timedelta(days=20),
        close_date=today - timedelta(days=17),
        allotment_date=today - timedelta(days=15),
        listing_date=today - timedelta(days=12),
        registrar_name="KFin Technologies Limited",
        registrar_url="https://kfintech.com",
        rhp_url="https://www.sebi.gov.in/hyundai-rhp.pdf",
        primary_source_id=ds_upstox.id
    )

    db.add_all([ipo_swiggy, ipo_hyundai])
    db.flush()

    # 3. Create Time-Series GMP Observations (Multi-source, append-only, strictly increasing timestamps)
    t1 = now - timedelta(hours=24)
    t2 = now - timedelta(hours=18)
    t3 = now - timedelta(hours=12)
    t4 = now - timedelta(hours=1)

    gmp1 = GMPHistory(
        ipo_id=ipo_swiggy.id,
        source_id=ds_apify.id,
        gmp_price=12.00,
        gmp_percent=3.08,
        estimated_listing_price=402.00,
        subject_to_sauda=300.00,
        observation_time=t1
    )
    gmp2 = GMPHistory(
        ipo_id=ipo_swiggy.id,
        source_id=ds_investorgain.id,
        gmp_price=11.50,
        gmp_percent=2.95,
        estimated_listing_price=401.50,
        subject_to_sauda=280.00,
        observation_time=t2
    )
    gmp3 = GMPHistory(
        ipo_id=ipo_swiggy.id,
        source_id=ds_apify.id,
        gmp_price=18.00,
        gmp_percent=4.62,
        estimated_listing_price=408.00,
        subject_to_sauda=450.00,
        observation_time=t3
    )
    gmp4 = GMPHistory(
        ipo_id=ipo_swiggy.id,
        source_id=ds_apify.id,
        gmp_price=22.00,
        gmp_percent=5.64,
        estimated_listing_price=412.00,
        subject_to_sauda=550.00,
        observation_time=t4
    )

    db.add_all([gmp1, gmp2, gmp3, gmp4])

    # 4. Create Time-Series Subscription Observations
    sub1 = SubscriptionHistory(
        ipo_id=ipo_swiggy.id,
        source_id=ds_upstox.id,
        qib_x=0.10,
        nii_x=0.25,
        b_nii_x=0.20,
        s_nii_x=0.30,
        retail_x=0.84,
        employee_x=1.15,
        overall_x=0.55,
        observation_time=t3
    )
    sub2 = SubscriptionHistory(
        ipo_id=ipo_swiggy.id,
        source_id=ds_upstox.id,
        qib_x=6.02,
        nii_x=4.15,
        b_nii_x=4.50,
        s_nii_x=3.45,
        retail_x=1.14,
        employee_x=1.65,
        overall_x=3.59,
        observation_time=t4
    )
    db.add_all([sub1, sub2])

    # 5. Create Notification Log
    notif = Notification(
        ipo_id=ipo_swiggy.id,
        telegram_chat_id="123456789",
        notification_type=NotificationType.GMP_SPIKE,
        title="🚀 GMP Alert: Swiggy Limited",
        message="Swiggy GMP rose +22.2% from ₹18.00 to ₹22.00 (Est Return: 5.64%).",
        status=NotificationStatus.SENT,
        sent_at=now,
        source_id=ds_apify.id
    )
    db.add(notif)

    # 6. Create API Request SLA Log
    api_log = APIRequest(
        source_id=ds_upstox.id,
        endpoint="/v2/ipos",
        http_method="GET",
        status_code=200,
        response_time_ms=142,
        request_timestamp=now
    )
    db.add(api_log)

    # 7. Create Workflow Telemetry Log
    wf_log = WorkflowHealth(
        workflow_name="WF-01: Ingestion Sync Cron",
        n8n_execution_id="exec_987654321",
        status=HealthStatus.SUCCESS,
        metrics={"fetched_ipos": 5, "updated_gmp": 3, "duration_ms": 840},
        last_heartbeat=now
    )
    db.add(wf_log)

    db.commit()
    print("Database successfully seeded!")
