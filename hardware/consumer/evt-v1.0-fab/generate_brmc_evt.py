#!/usr/bin/env python3
from pathlib import Path
import uuid, json, csv
OUT=Path(__file__).resolve().parent
def uid(): return str(uuid.uuid4())
class Board:
    def __init__(self,name,w,h):
        self.name=name; self.w=w; self.h=h; self.nets={"":0}; self.fps=[]; self.segs=[]; self.vias=[]; self.texts=[]; self.pads=[]
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
    def route_bus(self):
        netpads={}
        for p in self.pads:
            if p["net"]: netpads.setdefault(p["net"],[]).append(p)
        used=[n for n,p in netpads.items() if len(p)>=2]
        ys=[16.5+i*1.25 for i in range(38)]
        if len(used)>len(ys): raise RuntimeError((len(used),len(ys)))
        lanes={n:y for n,y in zip(sorted(used),ys)}

        # First establish each pad's vertical fanout corridor.  Different
        # connector-row classes live on separate signal layers.
        endpoints=[]
        for n,plist in netpads.items():
            if len(plist)<2: continue
            by=lanes[n]
            for p in plist:
                if p["y"] > 68.5:
                    ly="In3.Cu"; ex=p["x"]+1.25
                elif p["y"] > 67.5:
                    ly="In1.Cu"; ex=p["x"]
                elif p["y"] >= 60:
                    ly="F.Cu"; ex=p["x"]
                else:
                    ly="In4.Cu"; ex=p["x"]
                endpoints.append({"net":n,"p":p,"by":by,"ly":ly,"ex":ex})

        verticals=[]
        for e in endpoints:
            verticals.append({"x":e["ex"],"y0":min(e["p"]["y"],e["by"]),
                              "y1":max(e["p"]["y"],e["by"]),"ly":e["ly"],"net":e["net"],"e":e})

        # A through-via intersects every copper layer. Place it in a locally
        # clear slot instead of blindly at the vertical trace x-coordinate.
        VIA_SIZE=0.55; VIA_DRILL=0.30; TRACK_W=0.20; CLEAR=0.20
        need=VIA_SIZE/2 + TRACK_W/2 + CLEAR
        def spans(v,y): return v["y0"]-0.001 <= y <= v["y1"]+0.001
        def safe_via(e,vx):
            if vx < 1.0 or vx > self.w-1.0: return False
            for v in verticals:
                if v["net"]==e["net"]: continue
                if spans(v,e["by"]) and abs(vx-v["x"]) < need-1e-6:
                    return False
            lo,hi=sorted((e["ex"],vx))
            for v in verticals:
                if v["net"]==e["net"] or v["ly"]!=e["ly"]: continue
                if spans(v,e["by"]) and lo+1e-6 < v["x"] < hi-1e-6:
                    return False
            return True
        def choose_via(e):
            for step in range(0,121):
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
                p=e["p"]; ex=e["ex"]; vx=e["vx"]; ly=e["ly"]
                if abs(ex-p["x"])>1e-6:
                    self.segs.append((p["x"],p["y"],ex,p["y"],TRACK_W,ly,nid))
                self.segs.append((ex,p["y"],ex,by,TRACK_W,ly,nid))
                if abs(vx-ex)>1e-6:
                    self.segs.append((ex,by,vx,by,TRACK_W,ly,nid))
                self.vias.append((vx,by,VIA_SIZE,VIA_DRILL,nid)); vxs.append(vx)
            self.segs.append((min(vxs),by,max(vxs),by,TRACK_W,"B.Cu",nid))
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
    def write(self,path):
        layers='(layers\n  (0 "F.Cu" signal)\n  (2 "In1.Cu" power)\n  (4 "In2.Cu" power)\n  (6 "In3.Cu" signal)\n  (8 "In4.Cu" signal)\n  (31 "B.Cu" signal)\n  (36 "B.SilkS" user "B.Silkscreen")\n  (37 "F.SilkS" user "F.Silkscreen")\n  (38 "B.Mask" user)\n  (39 "F.Mask" user)\n  (44 "Edge.Cuts" user)\n  (46 "B.CrtYd" user "B.Courtyard")\n  (47 "F.CrtYd" user "F.Courtyard")\n  (48 "B.Fab" user)\n  (49 "F.Fab" user)\n)'
        s=['(kicad_pcb','  (version 20240108)','  (generator "pcbnew")','  (generator_version "8.0")','  (general (thickness 1.6) (legacy_teardrops no))','  (paper "A4")','  (title_block (title "BRMC Consumer EVT Backplane") (date "2026-09-02") (rev "1.0-EVT") (company "BattleReef"))','  '+layers.replace('\n','\n  '),'  (setup (pad_to_mask_clearance 0) (allow_soldermask_bridges_in_footprints no))']
        for n,i in sorted(self.nets.items(),key=lambda kv:kv[1]): s.append(f'  (net {i} "{n}")')
        for fp in self.fps: s+=self._fp(fp)
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
b.add_text("BRMC CONSUMER EVT v1.0",110,75,1.4); b.add_text("MODULAR PROTOTYPE BACKPLANE - NOT FOR SALE",110,3,1.0); b.add_text("No mains voltage on PCB",110,6,0.9)
b.route_bus(); b.write(OUT/"BRMC_Consumer_EVT_Backplane_v1.0.kicad_pcb")
(OUT/"BRMC_Consumer_EVT_Backplane_v1.0.kicad_pro").write_text(json.dumps({"board":{},"boards":[],"cvpcb":{},"erc":{},"libraries":{},"meta":{"filename":"BRMC_Consumer_EVT_Backplane_v1.0.kicad_pro","version":1},"net_settings":{"classes":[]},"pcbnew":{},"schematic":{},"text_variables":{"PRODUCT":"BRMC Consumer","REV":"1.0-EVT"}},indent=2),encoding="utf-8")
rows=[]
for fp in b.fps:
    for num,dx,dy,net in fp["coords"]: rows.append([fp["ref"],num,net,fp["val"]])
with (OUT/"BRMC_Consumer_EVT_Backplane_v1.0_Pinout.csv").open("w",newline="",encoding="utf-8") as f:
    w=csv.writer(f); w.writerow(["Connector","Pin","Net","Function"]); w.writerows(rows)
