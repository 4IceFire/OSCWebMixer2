#!/usr/bin/env python3
""" Simulate a DiGiCo SD9 for testing OSCWebMixer2. """
import re
from pythonosc import dispatcher, osc_server, udp_client

# --- CONFIGURATION ---
WEBMIXER_IP   = "127.0.0.1"  # your mixer’s OSC port
WEBMIXER_PORT = 8000
SIM_BIND_IP   = "0.0.0.0"     # <— listen on every interface
SIM_BIND_PORT = 9000
NUM_CHANNELS  = 8
NUM_AUX       = 4

client = udp_client.SimpleUDPClient(WEBMIXER_IP, WEBMIXER_PORT)

def handler(addr, *args):
    print(f"[Sim] {addr} {args}")
    if addr == "/Console/Channels/?":
        client.send_message("/Console/Input_Channels", [NUM_CHANNELS])
    m = re.match(r"^/Input_Channels/(\\d+)/Channel_Input/name/\\?$", addr)
    if m:
        i = int(m.group(1)); client.send_message(f"/Input_Channels/{i}/Channel_Input/name", [f"Ch{i}"])
    if addr == "/Console/Aux_Outputs/modes/?":
        modes = ["Mono"] * NUM_AUX
        client.send_message("/Console/Aux_Outputs/modes", modes)

     # Immediately reply with every Aux name so /aux can populate in one go
        for i in range(1, NUM_AUX + 1):
            client.send_message(f"/Aux_Outputs/{i}/Buss_Trim/name", [f"Aux{i}"])
        return

    m = re.match(r"^/Aux_Outputs/(\\d+)/Buss_Trim/name/\\?$", addr)
    if m:
        i = int(m.group(1)); client.send_message(f"/Aux_Outputs/{i}/Buss_Trim/name", [f"Aux{i}"])
    m = re.match(r"^/Aux_Outputs/(\\d+)/Buss_Trim/level/\\?$", addr)
    if m:
        i = int(m.group(1)); client.send_message(f"/Aux_Outputs/{i}/Buss_Trim/level", [0.0])

if __name__ == "__main__":
    print(f"Simulator on {SIM_BIND_IP}:{SIM_BIND_PORT}, forwarding → {WEBMIXER_IP}:{WEBMIXER_PORT}")
    disp = dispatcher.Dispatcher()
    disp.set_default_handler(handler)
    server = osc_server.ThreadingOSCUDPServer((SIM_BIND_IP, SIM_BIND_PORT), disp)
    server.serve_forever()
