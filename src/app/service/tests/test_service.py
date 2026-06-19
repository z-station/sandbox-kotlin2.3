# Тесты запускать только в контейнере!
import subprocess
from unittest.mock import call

import pytest

from app import config, messages
from app.entities import DebugData, TestData, TestsData
from app.service import exceptions
from app.service.entities import ExecuteResult, KotlinFile
from app.service.exceptions import CheckerException
from app.service.main import KotlinService

INVALID_SYNTAX_DETAILS = (
    'invalid syntax. Perhaps you forgot a comma? '
    '(<string>, line 1)'
)


def test_execute__console_result__ok():

    # arrange
    data_in = '2 3'
    code = (
        'fun main() {\n'
        '    val scanner = java.util.Scanner(System.`in`)\n'
        '    val a = scanner.nextInt()\n'
        '    val b = scanner.nextInt()\n'
        '    println(a + b)\n'
        '}\n'
    )
    file = KotlinFile(code)
    KotlinService._compile(file)

    # act
    exec_result = KotlinService._execute(file=file, data_in=data_in)

    # assert
    assert exec_result.result == '5'
    assert exec_result.error is None
    file.remove()


def test_execute__data_in_is_integer__ok():

    # arrange
    data_in = (
        '6\n'
        '50'
    )
    code = (
        'fun main() {\n'
        '    val scanner = java.util.Scanner(System.`in`)\n'
        '    val n = scanner.nextInt()\n'
        '    val k = scanner.nextInt()\n'
        '    println(k / n)\n'
        '    println(k - (k / n) * n)\n'
        '}\n'
    )
    file = KotlinFile(code)
    KotlinService._compile(file)

    # act
    exec_result = KotlinService._execute(file=file, data_in=data_in)

    # assert
    assert exec_result.result == (
        '8\n'
        '2'
    )
    assert exec_result.error is None
    file.remove()


def test_execute__readln_three_integers__ok():

    # arrange
    data_in = (
        '1\n'
        '2\n'
        '3'
    )
    code = (
        'fun main() {\n'
        '    val a = readln().toInt()\n'
        '    val b = readln().toInt()\n'
        '    val c = readln().toInt()\n'
        '    println(a + b + c)\n'
        '}\n'
    )
    file = KotlinFile(code)
    KotlinService._compile(file)

    # act
    exec_result = KotlinService._execute(file=file, data_in=data_in)

    # assert
    assert exec_result.result == '6'
    assert exec_result.error is None
    file.remove()


def test_execute__empty_result__return_none():

    # arrange
    code = 'fun main() {\n}\n'
    file = KotlinFile(code)
    KotlinService._compile(file)

    # act
    exec_result = KotlinService._execute(file=file)

    # assert
    assert exec_result.result is None
    assert exec_result.error is None
    file.remove()


def test_execute__write_access__error():

    """ Тест работает только в контейнере
        т.к. там ограничены права на запись
        в файловую систему """

    # arrange
    code = (
        'fun main() {\n'
        '    val path = java.nio.file.Paths.get("/app/src")\n'
        '    if (java.nio.file.Files.isWritable(path)) {\n'
        '        println("Write allowed.")\n'
        '    } else {\n'
        '        println("Write Permission denied.")\n'
        '    }\n'
        '}\n'
    )
    file = KotlinFile(code)
    KotlinService._compile(file)

    # act
    exec_result = KotlinService._execute(file=file)

    # assert
    assert 'Write Permission denied.' in exec_result.result
    assert exec_result.error is None
    file.remove()


def test_execute__clear_error_message__ok(mocker):

    # arrange
    raw_error_message = (
        "/sandbox/1aab26a5-980c-4aae-9c8d-75cc78394aff/Main.kt:2: "
        "error: unresolved reference: adqeqwd\n"
    )
    clear_error_message = (
        "Main.kt:2: "
        "error: unresolved reference: adqeqwd"
    )
    code = 'fun main() {}'
    file = KotlinFile(code)
    popen_init_mock = mocker.patch.object(
        subprocess.Popen, '__init__', return_value=None
    )
    communicate_mock = mocker.patch(
        'subprocess.Popen.communicate',
        return_value=(None, raw_error_message)
    )
    kill_mock = mocker.patch('subprocess.Popen.kill')

    # act
    exec_result = KotlinService._execute(file=file)

    # assert
    popen_init_mock.assert_called()
    communicate_mock.assert_called_once_with(
        input=None,
        timeout=config.TIMEOUT
    )
    kill_mock.assert_called_once()
    assert exec_result.result is None
    assert exec_result.error == clear_error_message
    file.remove()


def test_execute__timeout__return_error(mocker):

    # arrange
    code = (
        'fun main() {\n'
        '    while (true) {}\n'
        '}\n'
    )
    file = KotlinFile(code)
    KotlinService._compile(file)
    timeout_mock = mocker.patch('app.config.TIMEOUT', 1)

    # act
    execute_result = KotlinService._execute(file=file)

    # assert
    assert timeout_mock == 1
    assert execute_result.error == messages.MSG_1
    assert execute_result.result is None
    file.remove()


def test_execute__proc_exception__raise_exception(mocker):

    # arrange
    code = 'fun main() {}'
    data_in = 'Some data in'
    file = KotlinFile(code)
    popen_init_mock = mocker.patch.object(
        subprocess.Popen, '__init__', return_value=None
    )
    communicate_mock = mocker.patch(
        'subprocess.Popen.communicate',
        side_effect=Exception()
    )
    kill_mock = mocker.patch('subprocess.Popen.kill')

    # act
    with pytest.raises(exceptions.ExecutionException) as ex:
        KotlinService._execute(file=file, data_in=data_in)

    # assert
    popen_init_mock.assert_called()
    assert ex.value.message == messages.MSG_6
    communicate_mock.assert_called_once_with(
        input=data_in,
        timeout=config.TIMEOUT
    )
    kill_mock.assert_called_once()
    file.remove()


def test_compile__ok(mocker):

    # arrange
    file_mock = mocker.Mock()
    kotlin_file_new_mock = mocker.patch.object(
        KotlinFile, '__new__', return_value=file_mock
    )
    popen_init_mock = mocker.patch.object(
        subprocess.Popen, '__init__', return_value=None
    )
    communicate_mock = mocker.patch(
        'subprocess.Popen.communicate',
        return_value=(None, None)
    )
    kill_mock = mocker.patch('subprocess.Popen.kill')

    # act
    KotlinService._compile(file_mock)

    # assert
    kotlin_file_new_mock.assert_not_called()
    popen_init_mock.assert_called()
    communicate_mock.assert_called_once_with(timeout=config.TIMEOUT)
    kill_mock.assert_called_once()


def test_check__true__ok():

    # arrange
    value = 'some value'
    right_value = 'some value'
    checker_func = (
        'def checker(right_value: str, value: str) -> bool:'
        '  return right_value == value'
    )

    # act
    check_result = KotlinService._check(
        checker_func=checker_func,
        right_value=right_value,
        value=value
    )

    # assert
    assert check_result is True


def test_check__false__ok():

    # arrange
    value = 'invalid value'
    right_value = 'some value'
    checker_func = (
        'def checker(right_value: str, value: str) -> bool:'
        '  return right_value == value'
    )

    # act
    check_result = KotlinService._check(
        checker_func=checker_func,
        right_value=right_value,
        value=value
    )

    # assert
    assert check_result is False


def test_debug__compile_is_success__ok(mocker):

    # arrange
    file_mock = mocker.Mock()
    remove_mock = mocker.Mock()
    file_mock.remove = remove_mock
    kotlin_file_new_mock = mocker.patch.object(
        KotlinFile, '__new__', return_value=file_mock
    )
    compile_mock = mocker.patch(
        'app.service.main.KotlinService._compile',
        return_value=None
    )
    execute_result = ExecuteResult(
        result='some execute code result',
        error='some compilation error'
    )
    execute_mock = mocker.patch(
        'app.service.main.KotlinService._execute',
        return_value=execute_result
    )
    data = DebugData(
        code='some code',
        data_in='some data_in'
    )

    # act
    debug_result = KotlinService.debug(data)

    # assert
    kotlin_file_new_mock.assert_called_once()
    remove_mock.assert_called_once()
    compile_mock.assert_called_once_with(file_mock)
    execute_mock.assert_called_once_with(
        file=file_mock,
        data_in=data.data_in
    )
    assert debug_result.result == execute_result.result
    assert debug_result.error == execute_result.error


def test_debug__compile_return_error__ok(mocker):

    # arrange
    compile_error = 'some error'
    file_mock = mocker.Mock()
    remove_mock = mocker.Mock()
    file_mock.remove = remove_mock
    kotlin_file_new_mock = mocker.patch.object(
        KotlinFile, '__new__', return_value=file_mock
    )
    compile_mock = mocker.patch(
        'app.service.main.KotlinService._compile',
        return_value=compile_error
    )
    execute_mock = mocker.patch('app.service.main.KotlinService._execute')
    data = DebugData(
        code='some code',
        data_in='some data_in'
    )

    # act
    debug_result = KotlinService.debug(data)

    # assert
    kotlin_file_new_mock.assert_called_once()
    remove_mock.assert_called_once()
    compile_mock.assert_called_once_with(file_mock)
    execute_mock.assert_not_called()
    assert debug_result.result is None
    assert debug_result.error == compile_error


def test_testing__compile_is_success__ok(mocker):

    # arrange
    file_mock = mocker.Mock()
    remove_mock = mocker.Mock()
    file_mock.remove = remove_mock
    kotlin_file_new_mock = mocker.patch.object(
        KotlinFile, '__new__', return_value=file_mock
    )
    compile_mock = mocker.patch(
        'app.service.main.KotlinService._compile',
        return_value=None
    )
    execute_result = ExecuteResult(
        result='some execute code result',
        error='some compilation error'
    )
    execute_mock = mocker.patch(
        'app.service.main.KotlinService._execute',
        return_value=execute_result
    )
    check_result = mocker.Mock()
    check_mock = mocker.patch(
        'app.service.main.KotlinService._check',
        return_value=check_result
    )
    test_1 = TestData(
        data_in='some test input 1',
        data_out='some test out 1'
    )
    test_2 = TestData(
        data_in='some test input 2',
        data_out='some test out 2'
    )
    data = TestsData(
        code='some code',
        checker='some checker',
        tests=[test_1, test_2]
    )

    # act
    testing_result = KotlinService.testing(data)

    # assert
    kotlin_file_new_mock.assert_called_once()
    compile_mock.assert_called_once_with(file_mock)
    assert execute_mock.call_args_list[0] == call(
        file=file_mock,
        data_in=test_1.data_in
    )
    assert execute_mock.call_args_list[1] == call(
        file=file_mock,
        data_in=test_2.data_in
    )
    assert check_mock.call_args_list[0] == call(
        checker_func=data.checker,
        right_value=test_1.data_out,
        value=execute_result.result
    )
    assert check_mock.call_args_list[1] == call(
        checker_func=data.checker,
        right_value=test_2.data_out,
        value=execute_result.result
    )
    remove_mock.assert_called_once()
    tests_result = testing_result.tests
    assert len(tests_result) == 2
    assert tests_result[0].result == execute_result.result
    assert tests_result[0].error == execute_result.error
    assert tests_result[0].ok == check_result
    assert tests_result[1].result == execute_result.result
    assert tests_result[1].error == execute_result.error
    assert tests_result[1].ok == check_result


def test_testing__compile_return_error__ok(mocker):

    # arrange
    file_mock = mocker.Mock()
    remove_mock = mocker.Mock()
    file_mock.remove = remove_mock
    kotlin_file_new_mock = mocker.patch.object(
        KotlinFile, '__new__', return_value=file_mock
    )
    compile_error = 'some error'
    compile_mock = mocker.patch(
        'app.service.main.KotlinService._compile',
        return_value=compile_error
    )
    execute_mock = mocker.patch('app.service.main.KotlinService._execute')
    check_mock = mocker.patch('app.service.main.KotlinService._check')
    test_1 = TestData(
        data_in='some test input 1',
        data_out='some test out 1'
    )
    test_2 = TestData(
        data_in='some test input 2',
        data_out='some test out 2'
    )
    data = TestsData(
        code='some code',
        checker='some checker',
        tests=[test_1, test_2]
    )

    # act
    testing_result = KotlinService.testing(data)

    # assert
    kotlin_file_new_mock.assert_called_once()
    compile_mock.assert_called_once_with(file_mock)
    execute_mock.assert_not_called()
    check_mock.assert_not_called()
    remove_mock.assert_called_once()
    tests_result = testing_result.tests
    assert len(tests_result) == 2
    assert tests_result[0].result is None
    assert tests_result[0].error == compile_error
    assert tests_result[0].ok is False
    assert tests_result[1].result is None
    assert tests_result[1].error == compile_error
    assert tests_result[1].ok is False


def test_compile__timeout__error(mocker):

    # arrange
    file_mock = mocker.Mock()
    kotlin_file_new_mock = mocker.patch.object(
        KotlinFile, '__new__', return_value=file_mock
    )
    popen_init_mock = mocker.patch.object(
        subprocess.Popen, '__init__', return_value=None
    )
    communicate_mock = mocker.patch(
        'subprocess.Popen.communicate',
        side_effect=subprocess.TimeoutExpired(
            cmd='',
            timeout=config.TIMEOUT
        )
    )
    kill_mock = mocker.patch('subprocess.Popen.kill')

    # act
    error = KotlinService._compile(file_mock)

    # assert
    kotlin_file_new_mock.assert_not_called()
    popen_init_mock.assert_called()
    assert error == messages.MSG_1
    communicate_mock.assert_called_once_with(timeout=config.TIMEOUT)
    kill_mock.assert_called_once()


def test_compile__exception__raise_exception(mocker):

    # arrange
    file_mock = mocker.Mock()
    kotlin_file_new_mock = mocker.patch.object(
        KotlinFile, '__new__', return_value=file_mock
    )
    popen_init_mock = mocker.patch.object(
        subprocess.Popen, '__init__', return_value=None
    )
    communicate_mock = mocker.patch(
        'subprocess.Popen.communicate',
        side_effect=Exception
    )
    kill_mock = mocker.patch('subprocess.Popen.kill')

    # act
    with pytest.raises(exceptions.CompileException) as ex:
        KotlinService._compile(file_mock)

    # assert
    kotlin_file_new_mock.assert_not_called()
    popen_init_mock.assert_called()
    assert ex.value.message == messages.MSG_7
    communicate_mock.assert_called_once_with(timeout=config.TIMEOUT)
    kill_mock.assert_called_once()


def test_compile__error__error(mocker):

    # arrange
    file_mock = mocker.Mock()
    kotlin_file_new_mock = mocker.patch.object(
        KotlinFile, '__new__', return_value=file_mock
    )
    compile_error = 'some error'
    popen_init_mock = mocker.patch.object(
        subprocess.Popen, '__init__', return_value=None
    )
    communicate_mock = mocker.patch(
        'subprocess.Popen.communicate',
        return_value=(None, compile_error)
    )
    kill_mock = mocker.patch('subprocess.Popen.kill')

    # act
    error = KotlinService._compile(file_mock)

    # assert
    kotlin_file_new_mock.assert_not_called()
    popen_init_mock.assert_called()
    assert error == compile_error
    communicate_mock.assert_called_once_with(timeout=config.TIMEOUT)
    kill_mock.assert_called_once()


def test_check__invalid_checker_func__raise_exception():

    # arrange
    checker_func = (
        'def my_checker(right_value: str, value: str) -> bool:'
        '  return right_value == value'
    )

    # act
    with pytest.raises(CheckerException) as ex:
        KotlinService._check(
            checker_func=checker_func,
            right_value='value',
            value='value'
        )

    # assert
    assert ex.value.message == messages.MSG_2


def test_check__no_return_instr__raise_exception():

    # arrange
    checker_func = (
        'def checker(right_value: str, value: str) -> bool:'
        '  result = right_value == value'
    )

    # act
    with pytest.raises(CheckerException) as ex:
        KotlinService._check(
            checker_func=checker_func,
            right_value='value',
            value='value'
        )

    # assert
    assert ex.value.message == messages.MSG_3


def test_check__return_not_bool__raise_exception():

    # arrange
    checker_func = (
        'def checker(right_value: str, value: str) -> bool:'
        '  return None'
    )

    # act
    with pytest.raises(CheckerException) as ex:
        KotlinService._check(
            checker_func=checker_func,
            right_value='value',
            value='value'
        )

    # assert
    assert ex.value.message == messages.MSG_4


def test_check__invalid_syntax__raise_exception():

    # arrange
    checker_func = (
        'def checker(right_value: str, value: str) -> bool:'
        '  include(invalid syntax here)'
        '  return True'
    )

    # act
    with pytest.raises(CheckerException) as ex:
        KotlinService._check(
            checker_func=checker_func,
            right_value='value',
            value='value'
        )

    # assert
    assert ex.value.message == messages.MSG_5
    assert ex.value.details == INVALID_SYNTAX_DETAILS

