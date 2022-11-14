import pytest, rich, inflection
from _pytest._code.code import ExceptionInfo, Code
from _pytest._code import filter_traceback
from _pytest.compat import get_real_func
from gherkin.parser import Parser


from .steps import get_step, NoStepError, registry

def pytest_collect_file(parent, file_path):
  if file_path.suffix == ".feature":
      print(type(file_path), file_path)
      return FeatureFile.from_parent(parent, path=file_path)

def pytest_collection_modifyitems(session, config, items):
    print("pytest_collection_modifyitems", items)

class FeatureFile(pytest.File):
    def collect(self):
        parser = Parser()
        with self.path.open() as o:
          doc = parser.parse(o.read())
          feature = doc['feature']
          name = inflection.underscore(inflection.parameterize(feature['name']))
          yield FeatureItem.from_parent(self, name=name, spec=feature)

class FeatureItem(pytest.Collector):
    def __init__(self, *, spec, **kwargs):
        super().__init__(**kwargs)
        self.spec = spec

    def collect(self):
        for item in self.spec['children']:
            if 'background' in item:
                spec = item['background']
                name = inflection.underscore(inflection.parameterize(spec['name']))
                yield BackgroundItem.from_parent(self, name=name, spec=spec)
            elif 'rule' in item:
                spec = item['rule']
                name = inflection.underscore(inflection.parameterize(spec['name']))
                yield RuleItem.from_parent(self, name=name, spec=spec)
            elif 'scenario' in item:
                spec = item['scenario']
                name = inflection.underscore(inflection.parameterize(spec['name']))
                yield ScenarioItem.from_parent(self, name=name, spec=spec)

    def repr_failure(self, excinfo):
        return "FEATURE FAILED"


class RuleItem(pytest.Collector):
    def __init__(self, *, spec, **kwargs):
        super().__init__(**kwargs)
        self.spec = spec

    def collect(self):
        for item in self.spec['children']:
            if 'background' in item:
                yield BackgroundItem.from_parent(self, name=item['background']['name'], spec=item['background'])
            elif 'scenario' in item:
                yield ScenarioItem.from_parent(self, name=item['scenario']['name'], spec=item['scenario'])

class ScenarioItem(pytest.Item):
    def __init__(self, *, spec, **kwargs):
        super().__init__(**kwargs)
        self.spec = spec
        self._obj = None

    @property
    def obj(self):
        return self._obj
    
    def runtest(self):
        for step in self.spec['steps']:
            self._obj = get_step(step['text'])
            self._obj()
        self._obj = None

    def repr_failure(self, excinfo):
        if isinstance(excinfo.value, NoStepError):
            return "\n".join(
                [
                    "unnable to find step for:",
                    f"  {excinfo.value.args!r}",
                    f"  {registry!r}"
                ]
            )
        else:
          repr = super().repr_failure(excinfo)
          repr.sections.insert(0, ("feature", "YES", '-'))
          print(repr.sections)
          return repr

    def _prunetraceback(self, excinfo: ExceptionInfo[BaseException]) -> None:
        if self._obj is not None and not self.config.getoption("fulltrace", False):
            code = Code.from_function(get_real_func(self.obj))
            path, firstlineno = code.path, code.firstlineno
            traceback = excinfo.traceback
            ntraceback = traceback.cut(path=path, firstlineno=firstlineno)
            if ntraceback == traceback:
                ntraceback = ntraceback.cut(path=path)
                if ntraceback == traceback:
                    ntraceback = ntraceback.filter(filter_traceback)
                    if not ntraceback:
                        ntraceback = traceback

            excinfo.traceback = ntraceback.filter()
            # issue364: mark all but first and last frames to
            # only show a single-line message for each frame.
            if self.config.getoption("tbstyle", "auto") == "auto":
                if len(excinfo.traceback) > 2:
                    for entry in excinfo.traceback[1:-1]:
                        entry.set_repr_style("short")


class BackgroundItem(ScenarioItem):
    pass

class StepItem(pytest.Item):
    def __init__(self, *, spec, **kwargs):
        super().__init__(**kwargs)
        self.spec = spec

    def runtest(self):
        step = get_step(self.spec['text'])
        step()

    def repr_failure(self, excinfo):
        if isinstance(excinfo.value, NoStepError):
            return "\n".join(
                [
                    "unnable to find step for:",
                    f"  {excinfo.value.args!r}",
                    f"  {registry!r}"
                ]
            )
        else:
            return repr(excinfo.value)
        

class FeatureException(Exception):
    pass

