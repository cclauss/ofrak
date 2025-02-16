import subprocess
import tempfile

import pytest

from ofrak.core.filesystem import format_called_process_error
from ofrak.resource import Resource
from pytest_ofrak.patterns.compressed_filesystem_unpack_modify_pack import (
    CompressedFileUnpackModifyPackPattern,
)


class TestLzoUnpackModifyPack(CompressedFileUnpackModifyPackPattern):
    @pytest.fixture(autouse=True)
    def create_test_file(self, tmpdir):
        d = tmpdir.mkdir("lzo")
        uncompressed_filename = d.join("hello.txt").realpath()
        with open(uncompressed_filename, "wb") as f:
            f.write(self.INITIAL_DATA)

        compressed_filename = d.join("hello.lzo").realpath()
        command = ["lzop", "-o", compressed_filename, uncompressed_filename]
        try:
            subprocess.run(command, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(format_called_process_error(e))

        self._test_file = compressed_filename

    async def verify(self, repacked_root_resource: Resource) -> None:
        compressed_data = await repacked_root_resource.get_data()
        with tempfile.NamedTemporaryFile(suffix=".lzo") as compressed_file:
            compressed_file.write(compressed_data)
            compressed_file.flush()

            command = ["lzop", "-d", "-f", "-c", compressed_file.name]
            try:
                result = subprocess.run(command, check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                raise RuntimeError(format_called_process_error(e))

            assert result.stdout == self.EXPECTED_REPACKED_DATA
