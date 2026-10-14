"""Previews for the house ads (Advertise here / vybesforge.com) -> /workspace/tent_previews/v5_house_ads/"""
import os,sys,shutil,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import tents_v11 as TV,tents_v11_preview as PV
OUT='/workspace/tent_previews/v5_house_ads';os.makedirs(OUT,exist_ok=True)
TV.verify(lambda s:None);ms,tex=PV.load();R=PV.render
def gp(x,z,w=80): g=TV.ground_fn((x-w,x+w,z-w,z+w))(x,z)[0];return (x-w,x+w,z-w,z+w,g-0.02)
shutil.copy(f'{TV.OUT}/house_advertise.png',f'{OUT}/0_sign_artwork.png')
R(ms,tex,(60,2.0,58),(60,2.6,45),55,ground=gp(60,50)).save(f'{OUT}/1_spawn_sign_front.png')
R(ms,tex,(60,1.15,72.5),(60,1.9,40),70,ground=gp(60,60)).save(f'{OUT}/1_spawn_sign_driver_view_front_row.png')
R(ms,tex,(88,1.15,83),(70,1.9,45),70,ground=gp(80,60)).save(f'{OUT}/1_spawn_sign_driver_view_back_row_east.png')
s=TV.SLOTS[0];GY0=gp(s[1],s[2],30)[4];R(ms,tex,(s[1]-10*np.sin(s[3]),GY0+1.7,s[2]-10*np.cos(s[3])),(s[1],GY0+1.4,s[2]),60,ground=gp(s[1],s[2],30)).save(f'{OUT}/2_tent_fallback_art_slot01.png')
shutil.copy(f'{TV.OUT}/tent_slot01.png',f'{OUT}/2_tent_fallback_artwork_slot01.png')
R(ms,tex,(-268,2.0,-326),(-278,1.9,-336),60,ground=gp(-270,-330)).save(f'{OUT}/3_drag_staging_sign_front.png')
R(ms,tex,(-255.75,1.15,-318),(-268,1.3,-340),75,ground=gp(-260,-330)).save(f'{OUT}/3_drag_staging_driver_view_west_lane.png')
R(ms,tex,(-12,2.0,-38),(-20,2.2,-33),60,ground=gp(-15,-35)).save(f'{OUT}/4_pit_straight_sign_front.png')
R(ms,tex,(35,1.15,-50),(-20,1.5,-40),60,ground=gp(10,-45)).save(f'{OUT}/4_pit_straight_driver_view.png')
print(sorted(os.listdir(OUT)))
