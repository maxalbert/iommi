import pytest
from django.test import RequestFactory
from iommi import (
    Column,
    Field,
    Form,
    Table,
)
from iommi.base import (
    build_long_path_by_path,
)
from iommi.page import (
    Fragment,
    Page,
)
from tri_declarative import Namespace
from tri_struct import Struct

from tests.helpers import (
    StubTraversable,
    req,
)
from tests.models import TFoo


def test_traverse():
    bar = Struct(
        _name='bar',
        declared_members=dict(
            baz=Struct(_name='baz'),
            buzz=Struct(_name='buzz'),
        ),
    )
    foo = Struct(
        _name='foo',
        declared_members=dict(
            bar=bar,
        ),
    )
    root = StubTraversable(
        _name='root',
        members=Struct(
            foo=foo
        ),
    )

    expected = {
        '': '',
        'foo': 'foo',
        'bar': 'foo/bar',
        'baz': 'foo/bar/baz',
        'buzz': 'foo/bar/buzz',
    }
    actual = build_long_path_by_path(root)
    assert actual.items() == expected.items()
    assert len(actual.keys()) == len(set(actual.keys()))


@pytest.mark.django_db
def test_traverse_on_iommi():
    class MyPage(Page):
        header = Fragment()
        some_form = Form(fields=Namespace(
            fisk=Field(),
        ))
        some_other_form = Form(fields=Namespace(
            fjomp=Field(),
            fisk=Field(),
        ))
        a_table = Table(
            model=TFoo,
            columns=Namespace(
                columns=Column(),
                fusk=Column(query__include=True, query__form__include=True),
            ),
        )

    page = MyPage(_name='root')

    actual = build_long_path_by_path(page)
    assert len(actual.keys()) == len(set(actual.keys()))
    page = page.bind(request=req('get'))

    assert page.iommi_path == ''
    assert page.parts.header.iommi_path == 'header'
    assert page.parts.some_form.fields.fisk.iommi_path == 'fisk'
    assert page.parts.some_other_form.fields.fisk.iommi_path == 'some_other_form/fisk'
    assert page.parts.a_table.query.form.iommi_path == 'form'
    assert page.parts.a_table.query.form.fields.fusk.iommi_path == 'fusk'
    assert page.parts.a_table.columns.fusk.iommi_path == 'a_table/fusk'


def test_evil_names_that_work():
    class EvilPage(Page):
        name = Fragment()
        parent = Fragment()
        path = Fragment()

    assert EvilPage().bind(request=req('get')).render_to_response().status_code == 200


def test_evil_names():
    class ErrorMessages(Page):
        bind = Fragment()
        iommi_style = Fragment()
        iommi_path = Fragment()
        iommi_dunderpath = Fragment()
        on_bind = Fragment()
        own_evaluate_parameters = Fragment()
        get_request = Fragment()

    with pytest.raises(Exception) as e:
        ErrorMessages()

    assert str(e.value) == 'The names bind, get_request, iommi_path, iommi_style, on_bind, own_evaluate_parameters are reserved by iommi, please pick other names'
