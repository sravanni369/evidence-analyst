import sys
from types import SimpleNamespace
import pandas as pd
import pytest
from ai import execute

class FakeSandbox:
    def __init__(self, fail=False):
        self.killed = False
        self.fail = fail
        self.files = SimpleNamespace(write=lambda p,d: None, read=lambda p: 'total\n5\n')
    def run_code(self, code, timeout):
        return SimpleNamespace(error=SimpleNamespace(name='RuntimeError') if self.fail else None)
    def kill(self):
        self.killed = True

@pytest.mark.parametrize('fail', [False, True])
def test_sandbox_teardown_on_success_and_failure(monkeypatch, fail):
    fake = FakeSandbox(fail)
    def create(**kwargs):
        assert kwargs == {'timeout':120, 'allow_internet_access':False}
        return fake
    monkeypatch.setenv('E2B_API_KEY','test-only')
    monkeypatch.setitem(sys.modules, 'e2b_code_interpreter', SimpleNamespace(Sandbox=SimpleNamespace(create=create)))
    if fail:
        with pytest.raises(RuntimeError): execute(pd.DataFrame({'x':[1]}), 'print(1)')
    else:
        assert execute(pd.DataFrame({'x':[1]}), 'print(1)').iloc[0,0] == 5
    assert fake.killed

def test_real_dspy_signature_with_scripted_model(monkeypatch):
    import dspy
    from ai import generate
    code = "import pandas as pd\npd.DataFrame({'total':[5]}).to_csv('/home/user/answer.csv',index=False)"
    model = dspy.utils.DummyLM([{'python_code':code}])
    monkeypatch.setenv('LLM_MODEL','test/scripted-model')
    monkeypatch.setattr(dspy,'LM',lambda *a,**kw:model)
    assert generate(pd.DataFrame({'x':[2,3]}),'Sum x') == code
