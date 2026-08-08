from typing import Dict, Any, Optional, List
from app.providers.base import BaseIPOProvider

class MockIPOProvider(BaseIPOProvider):
    """Mock IPO Data Provider for offline testing, unit tests, and validation."""

    def __init__(self, mock_response: Optional[Dict[str, Any]] = None, should_fail: bool = False):
        super().__init__(code="MOCK_PROVIDER", name="Mock IPO Test Provider")
        self.should_fail = should_fail
        self.mock_response = mock_response or {
            "status": "success",
            "data": [
                {
                    "symbol": "MOCK_SWIGGY",
                    "company_name": "Swiggy Limited Mock",
                    "bse_code": "544280",
                    "issue_type": "MAINBOARD",
                    "status": "OPEN",
                    "min_price": 371.0,
                    "max_price": 390.0,
                    "lot_size": 38,
                    "total_issue_size_cr": 11327.43,
                    "subscription": {
                        "qib_x": 6.02,
                        "nii_x": 4.15,
                        "retail_x": 1.14,
                        "overall_x": 3.59
                    }
                },
                {
                    "symbol": "MOCK_SME_TECH",
                    "company_name": "Mock SME Tech India Ltd",
                    "issue_type": "SME",
                    "status": "UPCOMING",
                    "min_price": 80.0,
                    "max_price": 85.0,
                    "lot_size": 1600,
                    "total_issue_size_cr": 45.50
                }
            ]
        }

    async def _do_fetch(self, status: Optional[str] = None) -> Dict[str, Any]:
        if self.should_fail:
            raise Exception("Mock provider simulated fetch failure")
        return self.mock_response
