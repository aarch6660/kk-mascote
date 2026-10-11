"""Composição linear do create_eye original (DXBC), incluindo UV do gradiente."""
import numpy as np

def linear(c):
 c=np.asarray(c,dtype=float)
 return np.where(c<=0.04045,c/12.92,((c+0.055)/1.055)**2.4)

def srgb(c):
 c=np.maximum(c,0)
 return np.where(c<=0.0031308,c*12.92,1.055*c**(1/2.4)-0.055)

def amostrar_clamp(im,u,v):
 h,w=im.shape[:2]
 x=np.clip(u*w-.5,0,w-1);y=np.clip(v*h-.5,0,h-1)
 x0=x.astype(int);y0=y.astype(int);x1=np.minimum(x0+1,w-1);y1=np.minimum(y0+1,h-1)
 fx=(x-x0)[...,None];fy=(y-y0)[...,None]
 return (im[y0,x0]*(1-fx)+im[y0,x1]*fx)*(1-fy)+(im[y1,x0]*(1-fx)+im[y1,x1]*fx)*fy

def compor_iris(main,mask,pupil):
 h,w=main.shape[:2];y,x=np.mgrid[:h,:w]
 u=(x+.5)/w;v=(y+.5)/h
 # ChaControl: offset=Lerp(-.5,.5,x), scale=Lerp(-1,1,x).
 fator=2*(1-(2*pupil['gradScale']-1));offset=pupil['gradOffsetY']-.5
 # PNG tem origem superior; a transformação do shader opera em UV Unity.
 grad=amostrar_clamp(linear(mask[:,:,:3]),.5+(u-.5)*fator,.5+(v-.5-offset)*fator)[:,:,0:1]
 tinta=linear(pupil['subColor'][:3])*(1-grad)+linear(pupil['baseColor'][:3])*grad
 cinza=linear(main[:,:,0:1])
 # Vivid Light do shader, misturado com Multiply pelo parâmetro _Blend.
 vivid=np.where(cinza>.5,tinta/np.maximum(2*(1-cinza),1e-8),1-(1-tinta)*.5/np.maximum(cinza,1e-8))
 vivid=np.clip(vivid,0,1)
 cor=tinta*cinza*(1-pupil['gradBlend'])+vivid*pupil['gradBlend']
 resultado=main.copy();resultado[:,:,:3]=np.clip(srgb(cor),0,1)
 resultado[:,:,3]*=pupil['baseColor'][3]
 return resultado
