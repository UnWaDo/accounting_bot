import pytest
from money.organization import Organization


@pytest.fixture
def org() -> Organization:
    return Organization(name='Some org', shortcut='org')


@pytest.mark.parametrize('value', [
    'Some org',
    'SOME ORG',
    'some org ',
    'Org',
    'org',
    'ORG',
])
def test_organization_equal_string(org: Organization, value: str):
    assert org == value


@pytest.mark.parametrize('value', [
    'Some ork',
    'Org some',
    'Ork',
    '',
    'lol',
])
def test_organization_unequal_string(org: Organization, value: str):
    assert org != value


def test_organization_equal_obj(org: Organization):
    other = Organization(name=org.name.upper(), shortcut=org.shortcut.upper())
    assert org == other


@pytest.mark.parametrize('name,shortcut', [('Lol company', 'org'),
                                           ('Some org', 'lol'),
                                           ('Lol org', 'lol')])
def test_organization_unequal_obj(org: Organization, name: str, shortcut: str):
    other = Organization(name=name, shortcut=shortcut)
    assert org != other
