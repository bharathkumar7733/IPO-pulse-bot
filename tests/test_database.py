import uuid
from datetime import datetime, timezone, date, timedelta
import pytest
from sqlalchemy import select, text, inspect, create_engine
from sqlalchemy.exc import IntegrityError
from alembic.config import Config
from alembic import command

from app.models import (
    Base,
    DataSource, SourceType,
    IPO, IssueType, IPOStatus,
    GMPHistory,
    SubscriptionHistory,
    Notification, NotificationStatus, NotificationType,
    APIRequest,
    WorkflowHealth, HealthStatus
)

def test_01_database_connects(db_session):
    """1. Verify Database connects."""
    result = db_session.execute(text("SELECT 1")).scalar()
    assert result == 1, "Database connection query must return 1"

def test_02_ipo_insert(db_session):
    """2. Verify IPO can be inserted."""
    ipo = IPO(
        symbol="TESTIPO",
        bse_code="599999",
        company_name="Test IPO Limited",
        issue_type=IssueType.MAINBOARD,
        status=IPOStatus.OPEN,
        min_price=100.00,
        max_price=110.00,
        lot_size=100
    )
    db_session.add(ipo)
    db_session.commit()
    
    assert ipo.id is not None
    assert isinstance(ipo.id, uuid.UUID)

def test_03_ipo_retrieve(db_session):
    """3. Verify IPO can be retrieved."""
    ipo = IPO(
        symbol="RETRIEVE_ME",
        company_name="Retrieve Tech Ltd",
        issue_type=IssueType.SME,
        status=IPOStatus.UPCOMING
    )
    db_session.add(ipo)
    db_session.commit()

    retrieved = db_session.scalars(select(IPO).where(IPO.symbol == "RETRIEVE_ME")).one()
    assert retrieved.company_name == "Retrieve Tech Ltd"
    assert retrieved.id == ipo.id

def test_04_duplicate_ipo_rejected(db_session):
    """4. Verify Duplicate IPO is rejected/handled by unique constraint."""
    ipo1 = IPO(symbol="DUP_SYMBOL", company_name="Company One")
    db_session.add(ipo1)
    db_session.commit()

    ipo2 = IPO(symbol="DUP_SYMBOL", company_name="Company Two")
    db_session.add(ipo2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

def test_05_gmp_observation_insert(db_session):
    """5. Verify GMP observation can be inserted."""
    ds = DataSource(code="SRC_GMP_1", name="GMP Source 1", source_type=SourceType.UNOFFICIAL_GMP)
    ipo = IPO(symbol="GMP_IPO_1", company_name="GMP Test Ltd")
    db_session.add_all([ds, ipo])
    db_session.commit()

    gmp = GMPHistory(
        ipo_id=ipo.id,
        source_id=ds.id,
        gmp_price=50.00,
        gmp_percent=10.00,
        estimated_listing_price=550.00,
        observation_time=datetime.now(timezone.utc)
    )
    db_session.add(gmp)
    db_session.commit()

    assert gmp.id is not None
    assert float(gmp.gmp_price) == 50.00

def test_06_multiple_gmp_observations_preserved(db_session):
    """6. Verify Multiple GMP observations for the same IPO are preserved (Append-only time series)."""
    ds1 = DataSource(code="SRC_A", name="Source A", source_type=SourceType.UNOFFICIAL_GMP)
    ds2 = DataSource(code="SRC_B", name="Source B", source_type=SourceType.UNOFFICIAL_GMP)
    ipo = IPO(symbol="MULTI_GMP", company_name="Multi GMP Ltd")
    db_session.add_all([ds1, ds2, ipo])
    db_session.commit()

    t1 = datetime.now(timezone.utc) - timedelta(hours=2)
    t2 = datetime.now(timezone.utc) - timedelta(hours=1)
    t3 = datetime.now(timezone.utc)

    gmp1 = GMPHistory(ipo_id=ipo.id, source_id=ds1.id, gmp_price=10.00, observation_time=t1)
    gmp2 = GMPHistory(ipo_id=ipo.id, source_id=ds2.id, gmp_price=12.00, observation_time=t2)
    gmp3 = GMPHistory(ipo_id=ipo.id, source_id=ds1.id, gmp_price=15.00, observation_time=t3)

    db_session.add_all([gmp1, gmp2, gmp3])
    db_session.commit()

    records = db_session.scalars(
        select(GMPHistory).where(GMPHistory.ipo_id == ipo.id).order_by(GMPHistory.observation_time.asc())
    ).all()

    assert len(records) == 3, "All 3 observations must be preserved without overwriting"
    assert [float(r.gmp_price) for r in records] == [10.00, 12.00, 15.00]

def test_07_subscription_history_stored(db_session):
    """7. Verify Subscription history can be stored."""
    ds = DataSource(code="SRC_SUB", name="Sub Source", source_type=SourceType.OFFICIAL)
    ipo = IPO(symbol="SUB_IPO", company_name="Sub Test Ltd")
    db_session.add_all([ds, ipo])
    db_session.commit()

    sub = SubscriptionHistory(
        ipo_id=ipo.id,
        source_id=ds.id,
        qib_x=2.50,
        nii_x=1.20,
        retail_x=3.80,
        overall_x=2.65,
        observation_time=datetime.now(timezone.utc)
    )
    db_session.add(sub)
    db_session.commit()

    retrieved = db_session.scalars(select(SubscriptionHistory).where(SubscriptionHistory.ipo_id == ipo.id)).one()
    assert float(retrieved.overall_x) == 2.65

def test_08_foreign_keys_work(db_session):
    """8. Verify Foreign keys work and reject invalid relationships."""
    invalid_gmp = GMPHistory(
        ipo_id=uuid.uuid4(),  # Random non-existent IPO UUID
        source_id=uuid.uuid4(),
        gmp_price=20.00,
        observation_time=datetime.now(timezone.utc)
    )
    db_session.add(invalid_gmp)
    
    # In SQLite, foreign key enforcement requires PRAGMA foreign_keys = ON;
    db_session.execute(text("PRAGMA foreign_keys = ON;"))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

def test_09_indexes_exist(db_session):
    """9. Verify Indexes exist where expected."""
    inspector = inspect(db_session.bind)
    
    ipo_indexes = [idx['name'] for idx in inspector.get_indexes('ipos')]
    gmp_indexes = [idx['name'] for idx in inspector.get_indexes('gmp_history')]
    sub_indexes = [idx['name'] for idx in inspector.get_indexes('subscription_history')]
    notif_indexes = [idx['name'] for idx in inspector.get_indexes('notifications')]

    # Check for index existence on critical columns
    assert any('symbol' in idx.get('column_names', []) for idx in inspector.get_indexes('ipos'))
    assert any('observation_time' in idx.get('column_names', []) for idx in inspector.get_indexes('gmp_history'))
    assert any('observation_time' in idx.get('column_names', []) for idx in inspector.get_indexes('subscription_history'))
    assert any('telegram_chat_id' in idx.get('column_names', []) for idx in inspector.get_indexes('notifications'))

def test_10_migrations_work_from_clean_db(tmp_path):
    """10. Verify Migrations work from a clean database using Alembic."""
    test_db_file = tmp_path / "clean_test.db"
    clean_url = f"sqlite:///{test_db_file}"
    
    # Run Alembic upgrade head on clean temporary DB
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", clean_url)
    
    command.upgrade(alembic_cfg, "head")

    # Inspect created tables in clean database
    clean_engine = create_engine(clean_url)
    inspector = inspect(clean_engine)
    tables = inspector.get_table_names()

    expected_tables = {
        'data_sources', 'ipos', 'gmp_history', 
        'subscription_history', 'notifications', 
        'api_requests', 'workflow_health', 'alembic_version'
    }
    
    for table in expected_tables:
        assert table in tables, f"Table {table} must be created by clean migration"
