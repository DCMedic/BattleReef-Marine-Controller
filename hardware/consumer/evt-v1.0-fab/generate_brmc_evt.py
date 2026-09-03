#!/usr/bin/env python3
from pathlib import Path
import csv
import itertools
import json
import uuid

OUT=Path(__file__).resolve().parent
UUID_NAMESPACE=uuid.UUID("bda3b68e-bf74-4b87-bec4-7fa1e742cb4d")
_uid_sequence=itertools.count()

def uid():
    """Return stable UUIDs so generated KiCad sources are reviewable in git."""
    return str(uuid.uuid5(UUID_NAMESPACE, f"brmc-consumer-evt-v1.0:{next(_uid_sequence)}"))

class Board:
    def __init__(self,name,w,h):
        self.name=name; self.w=w; self.h=h; self.nets={"":0}; self.fps=[]; self.segs=[]; self.vias=[]; self.texts=[]; self.pads=[]; self.holes=[]
    def netid(self,n):
        if n not in self.nets: self.nets[n]=len(self.nets)
        return self.nets[n]
    def add_header(self,ref,val,x,y,pins,pitch=2.54,rows=1):
        coords=[]
        if rows==1:
            n=len(pins); x0=-(n-1)*pitch/2
            for i,net in enumerate(pins): coords.append((str(i+1),x0+i*pitch,0,net))
            bodyw=max(4,n*pitch); bodyh=5
        else:
            assert len(pins)%2==0
            n=len(pins)//2; x0=-(n-1)*pitch/2
            for row in range(2):
                for i in range(n):
                    idx=row*n+i; coords.append((str(idx+1),x0+i*pitch,(row-.5)*pitch,pins[idx]))
            bodyw=max(4,n*pitch); bodyh=7
        fp={"ref":ref,"val":val,"x":x,"y":y,"coords":coords,"bodyw":bodyw,"bodyh":bodyh}; self.fps.append(fp)
        for num,dx,dy,net in coords:
            self.pads.append({"ref":ref,"num":num,"x":x+dx,"y":y+dy,"net":net}); self.netid(net)
    def add_text(self,text,x,y,size=1.2): self.texts.append((text,x,y,size))
    def add_mounting_hole(self,ref,x,y,drill=3.2):
        self.holes.append({"ref":ref,"x":x,"y":y,"drill":drill})
    @staticmethod
    def route_style(net):
        # Backplane power trunks meet the carried-forward EVT copper-width
        # requirements on B.Cu.  Short connector fan-outs neck down only as
        # needed for the 2.54 mm header pitch.
        if net == "GND":
            return {"fan":1.00,"bus":2.00,"via":1.00,"drill":0.50,"clear":0.20}
        if net == "5V_SYS":
            return {"fan":1.00,"bus":2.00,"via":1.00,"drill":0.50,"clear":0.20}
        if net == "24V_IN":
            return {"fan":0.80,"bus":1.50,"via":0.90,"drill":0.45,"clear":0.30}
        if net == "3V3_SYS":
            return {"fan":0.50,"bus":0.50,"via":0.90,"drill":0.45,"clear":0.20}
        if net in {"CAN_H","CAN_L","CAN_TX","CAN_RX","RS485_A","RS485_B","RS485_TX","RS485_RX","RS485_DE"}:
            return {"fan":0.25,"bus":0.25,"via":0.60,"drill":0.30,"clear":0.20}
        return {"fan":0.20,"bus":0.20,"via":0.55,"drill":0.30,"clear":0.20}
    def route_bus(self):
        netpads={}
        for p in self.pads:
            if p["net"]: netpads.setdefault(p["net"],[]).append(p)
        used=[n for n,p in netpads.items() if len(p)>=2]
        styles={n:self.route_style(n) for n in used}
        lanes={}
        cursor=15.0
        previous=None
        for n in sorted(used):
            style=styles[n]
            if previous is None:
                cursor += style["bus"]/2
            else:
                gap=max(previous["clear"],style["clear"])
                cursor += previous["bus"]/2 + gap + style["bus"]/2
            lanes[n]=round(cursor,3)
            previous=style
        if max(lanes.values()) > 63.0:
            raise RuntimeError(f"routing lanes exceed board corridor: {max(lanes.values())}")

        # First establish each pad's vertical fanout corridor.  Different
        # connector-row classes live on separate signal layers.
        endpoints=[]
        for n,plist in netpads.items():
            if len(plist)<2: continue
            by=lanes[n]
            for p in plist:
                if p["y"] > 68.5:
                    ly="F.Cu"; ex=p["x"]+1.25
                elif p["y"] > 67.5:
                    ly="F.Cu"; ex=p["x"]
                elif p["y"] >= 60:
                    ly="In2.Cu"; ex=p["x"]
                else:
                    ly="In3.Cu"; ex=p["x"]
                endpoints.append({"net":n,"p":p,"by":by,"ly":ly,"ex":ex,"style":styles[n]})

        verticals=[]
        for e in endpoints:
            verticals.append({"x":e["ex"],"y0":min(e["p"]["y"],e["by"]),
                              "y1":max(e["p"]["y"],e["by"]),"ly":e["ly"],"net":e["net"],
                              "width":e["style"]["fan"],"clear":e["style"]["clear"],"e":e})

        # A through-via intersects every copper layer. Place it in a locally
        # clear slot instead of blindly at the vertical trace x-coordinate.
        def spans(v,y): return v["y0"]-0.001 <= y <= v["y1"]+0.001
        def safe_via(e,vx):
            style=e["style"]
            if vx < style["via"]/2+0.5 or vx > self.w-style["via"]/2-0.5: return False
            for v in verticals:
                if v["net"]==e["net"]: continue
                need=style["via"]/2 + v["width"]/2 + max(style["clear"],v["clear"])
                if spans(v,e["by"]) and abs(vx-v["x"]) < need-1e-6:
                    return False
            lo,hi=sorted((e["ex"],vx))
            for v in verticals:
                if v["net"]==e["net"] or v["ly"]!=e["ly"]: continue
                need=e["style"]["fan"]/2 + v["width"]/2 + max(e["style"]["clear"],v["clear"])
                if spans(v,e["by"]) and lo-need+1e-6 < v["x"] < hi+need-1e-6:
                    return False
            return True
        def choose_via(e):
            for step in range(0,201):
                d=step*0.10
                cands=[e["ex"]] if step==0 else [e["ex"]-d,e["ex"]+d]
                for vx in cands:
                    if safe_via(e,vx): return round(vx,3)
            raise RuntimeError(f'no safe via for {e}')

        bynet={}
        for e in endpoints:
            e["vx"]=choose_via(e); bynet.setdefault(e["net"],[]).append(e)

        for n,elist in bynet.items():
            nid=self.netid(n); by=lanes[n]; vxs=[]
            for e in elist:
                p=e["p"]; ex=e["ex"]; vx=e["vx"]; ly=e["ly"]; style=e["style"]
                if abs(ex-p["x"])>1e-6:
                    self.segs.append((p["x"],p["y"],ex,p["y"],style["fan"],ly,nid))
                self.segs.append((ex,p["y"],ex,by,style["fan"],ly,nid))
                if abs(vx-ex)>1e-6:
                    self.segs.append((ex,by,vx,by,style["fan"],ly,nid))
                self.vias.append((vx,by,style["via"],style["drill"],nid)); vxs.append(vx)
            self.segs.append((min(vxs),by,max(vxs),by,style["bus"],"B.Cu",nid))
    def _fp(self,fp):
        q=lambda v:f'{v:.3f}'
        out=[f'  (footprint "BRMC:HDR_{fp["ref"]}"','    (layer "F.Cu")',f'    (uuid "{uid()}")',f'    (at {q(fp["x"])} {q(fp["y"])})',
             f'    (property "Reference" "{fp["ref"]}" (at 0 -4 0) (layer "F.SilkS") (uuid "{uid()}") (effects (font (size 1 1) (thickness 0.15))))',
             f'    (property "Value" "{fp["val"]}" (at 0 4 0) (layer "F.Fab") hide (uuid "{uid()}") (effects (font (size 1 1) (thickness 0.15))))',
             f'    (fp_rect (start {q(-fp["bodyw"]/2)} {q(-fp["bodyh"]/2)}) (end {q(fp["bodyw"]/2)} {q(fp["bodyh"]/2)}) (stroke (width 0.2) (type default)) (fill none) (layer "F.SilkS") (uuid "{uid()}"))']
        for num,dx,dy,net in fp["coords"]:
            shape="rect" if num=="1" else "circle"
            out.append(f'    (pad "{num}" thru_hole {shape} (at {q(dx)} {q(dy)}) (size 1.8 1.8) (drill 1.0) (layers "*.Cu" "*.Mask") (net {self.netid(net)} "{net}") (pinfunction "{net}") (pintype "passive") (uuid "{uid()}"))')
        out.append('  )'); return out
    def _hole(self,hole):
        q=lambda v:f'{v:.3f}'
        return [f'  (footprint "BRMC:MOUNT_M3_{hole["ref"]}"',
                '    (layer "F.Cu")',f'    (uuid "{uid()}")',
                f'    (at {q(hole["x"])} {q(hole["y"])})',
                f'    (property "Reference" "{hole["ref"]}" (at 0 0 0) (layer "F.Fab") hide (uuid "{uid()}") (effects (font (size 1 1) (thickness 0.15))))',
                '    (property "Value" "MountingHole_3.2mm_M3" (at 0 0 0) (layer "F.Fab") hide (uuid "'+uid()+'") (effects (font (size 1 1) (thickness 0.15))))',
                f'    (pad "" np_thru_hole circle (at 0 0) (size {q(hole["drill"])} {q(hole["drill"])}) (drill {q(hole["drill"])}) (layers "*.Cu" "*.Mask") (uuid "{uid()}"))',
                '  )']
    def write(self,path):
        layers='(layers\n  (0 "F.Cu" signal)\n  (2 "In1.Cu" power)\n  (4 "In2.Cu" power)\n  (6 "In3.Cu" signal)\n  (8 "In4.Cu" signal)\n  (31 "B.Cu" signal)\n  (36 "B.SilkS" user "B.Silkscreen")\n  (37 "F.SilkS" user "F.Silkscreen")\n  (38 "B.Mask" user)\n  (39 "F.Mask" user)\n  (44 "Edge.Cuts" user)\n  (46 "B.CrtYd" user "B.Courtyard")\n  (47 "F.CrtYd" user "F.Courtyard")\n  (48 "B.Fab" user)\n  (49 "F.Fab" user)\n)'
        s=['(kicad_pcb','  (version 20240108)','  (generator "pcbnew")','  (generator_version "8.0")','  (general (thickness 1.6) (legacy_teardrops no))','  (paper "A4")','  (title_block (title "BRMC Consumer EVT Backplane") (date "2026-09-02") (rev "1.0-EVT") (company "BattleReef"))','  '+layers.replace('\n','\n  '),'  (setup (pad_to_mask_clearance 0) (allow_soldermask_bridges_in_footprints no))']
        for n,i in sorted(self.nets.items(),key=lambda kv:kv[1]): s.append(f'  (net {i} "{n}")')
        for fp in self.fps: s+=self._fp(fp)
        for hole in self.holes: s+=self._hole(hole)
        s.append(f'  (gr_rect (start 0 0) (end {self.w} {self.h}) (stroke (width 0.25) (type default)) (fill none) (layer "Edge.Cuts") (uuid "{uid()}"))')
        for text,x,y,size in self.texts: s.append(f'  (gr_text "{text}" (at {x:.3f} {y:.3f}) (layer "F.SilkS") (uuid "{uid()}") (effects (font (size {size} {size}) (thickness 0.18))))')
        for x1,y1,x2,y2,w,ly,nid in self.segs: s.append(f'  (segment (start {x1:.3f} {y1:.3f}) (end {x2:.3f} {y2:.3f}) (width {w}) (layer "{ly}") (net {nid}) (uuid "{uid()}"))')
        for x,y,sz,dr,nid in self.vias: s.append(f'  (via (at {x:.3f} {y:.3f}) (size {sz}) (drill {dr}) (layers "F.Cu" "B.Cu") (net {nid}) (uuid "{uid()}"))')
        s.append(')'); Path(path).write_text('\n'.join(s),encoding='utf-8')
b=Board("BRMC_EVT_Backplane",220,78)
b.add_header("J_CM5","CM5_IO_HARNESS",25,68,["5V_SYS","GND","I2C_SCL","I2C_SDA","CM5_TX","CM5_RX","CM5_HEARTBEAT","SAFETY_ACK","SPI_SCK","SPI_MISO","SPI_MOSI","SPI_CS0","GPIO_AUX0","GPIO_AUX1","3V3_SYS","GND"],rows=2)
b.add_header("J_MCU","STM32G0B1_CORE",75,68,["5V_SYS","GND","3V3_SYS","CM5_TX","CM5_RX","CM5_HEARTBEAT","SAFETY_ACK","I2C_SCL","I2C_SDA","SPI_SCK","SPI_MISO","SPI_MOSI","SPI_CS0","CAN_TX","CAN_RX","RS485_TX","RS485_RX","RS485_DE","SAFETY_ENABLE","TEMP_DATA","SWDIO","SWCLK","NRST","GND"],rows=2)
b.add_header("J_PH","ATLAS_EZO_PH_ISO",125,68,["5V_SYS","GND","I2C_SCL","I2C_SDA","PH_OFF"])
b.add_header("J_ORP","ATLAS_EZO_ORP_ISO",150,68,["5V_SYS","GND","I2C_SCL","I2C_SDA","ORP_OFF"])
b.add_header("J_EC","ATLAS_EZO_EC_ISO",175,68,["5V_SYS","GND","I2C_SCL","I2C_SDA","EC_OFF"])
b.add_header("J_TEMP","DIGITAL_TEMP",202,68,["3V3_SYS","GND","TEMP_DATA","TEMP_AUX"])
b.add_header("J_PWR","POWER_HARNESS",15,10,["24V_IN","GND","5V_SYS","GND","12V_SYS","GND"])
b.add_header("J_CAN","ISO_CAN_FD_MODULE",52,10,["5V_SYS","GND","CAN_TX","CAN_RX","CAN_H","CAN_L"])
b.add_header("J_485","ISO_RS485_MODULE",83,10,["5V_SYS","GND","RS485_TX","RS485_RX","RS485_DE","RS485_A","RS485_B"])
b.add_header("J_AO","MODBUS_0_10V_8CH",120,10,["24V_IN","GND","RS485_A","RS485_B"])
b.add_header("J_PWRMOD","BRMC_POWER_MODULE_BUS",150,10,["24V_IN","GND","CAN_H","CAN_L","RS485_A","RS485_B","SAFETY_ENABLE","GND"])
b.add_header("J_SAFE","SAFETY_RELAY_DRIVE",180,10,["SAFETY_ENABLE","GND","24V_IN","GND"])
b.add_header("J_SVC","SERVICE_DEBUG",205,10,["3V3_SYS","GND","SWDIO","SWCLK","NRST","CM5_TX","CM5_RX","GND"])
# Six symmetric M3 clearance holes reproduce the v0.9 main-board mounting
# intent (three columns by two rows) in the 220 x 78 mm coordinate system.
for ref,x,y in [("H1",7,7),("H2",110,7),("H3",213,7),("H4",7,71),("H5",110,71),("H6",213,71)]:
    b.add_mounting_hole(ref,x,y)
b.add_text("BRMC CONSUMER EVT v1.0",110,75,1.4); b.add_text("MODULAR PROTOTYPE BACKPLANE - NOT FOR SALE",110,3,1.0); b.add_text("No mains voltage on PCB",110,6,0.9)
b.route_bus(); b.write(OUT/"BRMC_Consumer_EVT_Backplane_v1.0.kicad_pcb")
(OUT/"BRMC_Consumer_EVT_Backplane_v1.0.kicad_pro").write_text(json.dumps({"board":{},"boards":[],"cvpcb":{},"erc":{},"libraries":{},"meta":{"filename":"BRMC_Consumer_EVT_Backplane_v1.0.kicad_pro","version":1},"net_settings":{"classes":[]},"pcbnew":{},"schematic":{},"text_variables":{"PRODUCT":"BRMC Consumer","REV":"1.0-EVT"}},indent=2),encoding="utf-8")
rows=[]
for fp in b.fps:
    for num,dx,dy,net in fp["coords"]: rows.append([fp["ref"],num,net,fp["val"]])
with (OUT/"BRMC_Consumer_EVT_Backplane_v1.0_Pinout.csv").open("w",newline="",encoding="utf-8") as f:
    w=csv.writer(f); w.writerow(["Connector","Pin","Net","Function"]); w.writerows(rows)

(OUT/"BRMC_Consumer_EVT_Backplane_v1.0.kicad_dru").write_text('''(version 1)

# Keep L2 and L5 free of routed tracks so reviewed GND pours can be added as
# the two continuous reference layers in the controlled six-layer stackup.
(rule "No tracks on L2 ground reference"
  (layer "In1.Cu")
  (constraint disallow track))

(rule "No tracks on L5 ground reference"
  (layer "In4.Cu")
  (constraint disallow track))

(rule "24V fanout width"
  (condition "A.NetName == '24V_IN' && A.Type == 'Track'")
  (constraint track_width (min 0.80mm)))

(rule "24V trunk width"
  (layer "B.Cu")
  (condition "A.NetName == '24V_IN' && A.Type == 'Track'")
  (constraint track_width (min 1.50mm)))

(rule "24V clearance"
  (condition "A.NetName == '24V_IN' || B.NetName == '24V_IN'")
  (constraint clearance (min 0.30mm)))

(rule "5V and ground fanout width"
  (condition "(A.NetName == '5V_SYS' || A.NetName == 'GND') && A.Type == 'Track'")
  (constraint track_width (min 1.00mm)))

(rule "5V and ground trunk width"
  (layer "B.Cu")
  (condition "(A.NetName == '5V_SYS' || A.NetName == 'GND') && A.Type == 'Track'")
  (constraint track_width (min 2.00mm)))

(rule "3V3 width"
  (condition "A.NetName == '3V3_SYS' && A.Type == 'Track'")
  (constraint track_width (min 0.50mm)))

(rule "Field-bus width"
  (condition "(A.NetName == 'CAN_H' || A.NetName == 'CAN_L' || A.NetName == 'CAN_TX' || A.NetName == 'CAN_RX' || A.NetName == 'RS485_A' || A.NetName == 'RS485_B' || A.NetName == 'RS485_TX' || A.NetName == 'RS485_RX' || A.NetName == 'RS485_DE') && A.Type == 'Track'")
  (constraint track_width (min 0.25mm)))
''',encoding="utf-8")
