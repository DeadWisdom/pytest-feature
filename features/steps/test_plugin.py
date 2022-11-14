from pytest_feature import step

@step("we have tests")
def _():
  assert True

@step("we run pytest")
def _():
  assert False, "This one fails"

def test_in_here():
    assert False

