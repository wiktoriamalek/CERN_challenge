import asyncio
from asyncio import AbstractEventLoop

import pytest
import os
import pytest_asyncio

from plc.plc_client import PLCClient
from plc.plc_simulator import PLCSimulator
from main import main

SERVER_PORT = 4840
SERVER_URL = f"opc.tcp://localhost:{SERVER_PORT}/freeopcua/server/"
CLIENT_TIMEOUT = 5  # seconds



@pytest_asyncio.fixture(scope="function")
async def plc() -> PLCClient:
    """ Instance of the OPC UA client to communicate with the simulator """
    plc = PLCClient(url=SERVER_URL, timeout=CLIENT_TIMEOUT)
    await plc.init()
    yield plc
    await plc.disconnect()



class TestGRAFCET:

    # Press START button and check that tank is filling
    @pytest.mark.asyncio
    async def test_start_prefilling(self, plc: PLCClient):
        # Assert initial conditions
        x = await plc.get_object_value("DQ0")
        assert await plc.get_object_value("DQ0") == False  # Tank is not filling
        assert await plc.get_object_value("DQ1") == False  # Tank is not discharging
        assert await plc.get_object_value("DQ2") == False  # Liquid is not heatinNg
        # assert await plc.get_object_value("DQ3")==False#Gate closed
        # Simulate pressing the START button
        await plc.set_object_pulse("DI0")  # Press START button
        await asyncio.sleep(1)  # Waiting for transition into next step

        # Assert actuations after pressing START button
        assert await plc.get_object_value("DQ0") == True  # Tank is filling
        assert await plc.get_object_value("DQ1") == False  # Tank is not discharging
        assert await plc.get_object_value("DQ2") == False  # Liquid is not heating
        # assert await plc.get_object_value("DQ3")==False chyba???

    # Test low level has been reached
    @pytest.mark.asyncio
    async def test_prefilling_ready(self, plc: PLCClient):
        await plc.set_object_value("DI6", True)
        await asyncio.sleep(1)

        assert await plc.get_object_value("DQ0") == False
        assert await plc.get_object_value("DQ1") == False
        assert await plc.get_object_value("DQ2") == False
        # assert await plc.get_object_value("DQ3")==False
        # sprawdzenie bledow i alarmow?

    # Test RUN button pressed
    @pytest.mark.asyncio
    async def test_run_button_pressed(self, plc: PLCClient):
        await plc.set_object_pulse("DI1")
        await asyncio.sleep(1)
        assert await plc.get_object_value("DQ0") == True

    # Test high level has been reached
    @pytest.mark.asyncio
    async def test_high_level_reached(self, plc: PLCClient):
        await plc.set_object_value("DI7", True)
        await asyncio.sleep(1)
        assert await plc.get_object_value("DQ0") == False
        assert await plc.get_object_value("DQ2") == True
        assert await plc.get_object_value("DQ1") == False
        # czy brama zamknieta

    # Test setpoint has been reached
    @pytest.mark.asyncio
    async def test_setpoint_reached(self, plc: PLCClient):
        await plc.set_object_value("AI0", 45.0)
        await asyncio.sleep(3)

        assert await plc.get_object_value("DQ2") == False
        assert await plc.get_object_value("DQ1") == True
        assert await plc.get_object_value("DQ3") == False

    # Test low level has been reached
    @pytest.mark.asyncio
    async def test_low_level_reached(self, plc: PLCClient):
        await plc.set_object_value("DI6", True)
        await asyncio.sleep(3)

        assert await plc.get_object_value("DQ1") == False
        assert await plc.get_object_value("DQ0") == True

    # Stop button
    @pytest.mark.asyncio
    async def test_stop_button(self, plc: PLCClient):
        await plc.set_object_pulse("DI1")
        await asyncio.sleep(1)

        filling_process = await plc.get_object_value("DQ0")
        heating_process = await plc.get_object_value("DQ2")
        discharging_process = await plc.get_object_value("DQ1")
        assert filling_process or heating_process or discharging_process

        await plc.set_object_pulse("DI2")
        await asyncio.sleep(1)

        assert await plc.get_object_value("DQ0") == False
        assert await plc.get_object_value("DQ1") == False
        assert await plc.get_object_value("DQ2") == False
        assert await plc.get_object_value("DQ3") == False

    # Add more test cases if needed
    # 3 koncowe podpunkty
