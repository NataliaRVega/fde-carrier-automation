from pydantic import BaseModel

class FMCSAResult(BaseModel):
	mc_number: str
	active_authority: bool

def verify_carrier(mc_number: str) ->FMCSAResult:
	"""
	Mock FMCSA verification
	
	For now:
	-MC 123456 is valid
	-Any other MC is invalid
	"""

	return FMCSAResult(
		mc_number=mc_number,
		active_authority=(mc_number == "123456"),
	)