import pytest
from subprocess import check_call
import os
import sys
from pathlib import Path


@pytest.fixture(scope="session")
def example_netstandard(tmpdir_factory):
    return build_example(tmpdir_factory, "netstandard20")


@pytest.fixture(scope="session")
def example_netcore(tmpdir_factory):
    return build_example(tmpdir_factory, "net60")


def build_example(tmpdir_factory, framework):
    out = Path(tmpdir_factory.mktemp(f"example-{framework}"))
    proj_path = Path(__file__).parent.parent / "example"

    check_call(["dotnet", "build", str(proj_path), "-o", str(out), "-f", framework])

    return out


def test_mono(example_netstandard):
    from clr_loader import get_mono

    mono = get_mono()
    asm = mono.get_assembly(example_netstandard / "example.dll")

    run_tests(asm)


def test_mono_debug(example_netstandard):
    from clr_loader import get_mono

    mono = get_mono(
        debug=True,
        jit_options=[
            "--debugger-agent=address=0.0.0.0:5831,transport=dt_socket,server=y"
        ],
    )
    asm = mono.get_assembly(example_netstandard / "example.dll")

    run_tests(asm)

def test_mono_signal_chaining(example_netstandard):
    from clr_loader import get_mono

    mono = get_mono(set_signal_chaining=True)
    asm = mono.get_assembly(example_netstandard / "example.dll")

    run_tests(asm)

def test_mono_set_dir(example_netstandard):
    from clr_loader import get_mono

    mono = get_mono(assembly_dir="/usr/lib", config_dir="/etc")
    asm = mono.get_assembly(example_netstandard / "example.dll")

    run_tests(asm)

def test_coreclr(example_netcore):
    from clr_loader import get_coreclr

    coreclr = get_coreclr(runtime_config=example_netcore / "example.runtimeconfig.json")
    asm = coreclr.get_assembly(example_netcore / "example.dll")

    run_tests(asm)


def test_coreclr_autogenerated_runtimeconfig(example_netstandard):
    from multiprocessing import get_context

    p = get_context("spawn").Process(
        target=_do_test_coreclr_autogenerated_runtimeconfig, args=(example_netstandard,)
    )
    p.start()
    p.join()
    p.close()


def _do_test_coreclr_autogenerated_runtimeconfig(example_netstandard):
    from clr_loader import get_coreclr

    coreclr = get_coreclr()
    asm = coreclr.get_assembly(example_netstandard / "example.dll")

    run_tests(asm)


@pytest.mark.skipif(
    sys.platform != "win32", reason=".NET Framework only exists on Windows"
)
def test_netfx(example_netstandard):
    from clr_loader import get_netfx

    netfx = get_netfx()
    asm = netfx.get_assembly(os.path.join(example_netstandard, "example.dll"))

    run_tests(asm)


def run_tests(asm):
    func = asm.get_function("Example.TestClass", "Test")
    test_data = b"testy mctestface"
    res = func(test_data)
    assert res == len(test_data)
