extends RefCounted
# Gerado por personagem/auditar_expression.py; não editar as fórmulas à mão.
# Assembly-CSharp.dll SHA256 3bae621468ca2de1b1f4fd428e2819d2835b23b64f0e104b2874d0615b5c5f2d
# ExpressionBone.LateUpdate 0x0600237b. Cada instrução emitida registra o offset IL.
func aplicar(e) -> void:
	var v0
	var v1
	var v2
	var v3
	var v4
	var v5
	var v6
	var v7
	var v8
	var v9
	var v10
	var v11
	var v12
	var v13
	var v14
	var v15
	var v16
	var v17
	var v18
	var v19
	var v20
	var v21
	var v22
	var v23
	var v24
	var v25
	var v26
	var v27
	var v28
	var v29
	var v30
	var v31
	var v32
	var v33
	var v34
	var v35
	var v36
	var v37
	var v38
	var v39
	var v40
	var v41
	var v42
	var v43
	var v44
	var v45
	var v46
	var v47
	var v48
	var v49
	var v50
	var v51
	var v52
	var v53
	var v54
	var v55
	var v56
	var v57
	var v58
	var v59
	var v60
	var v61
	var v62
	var v63
	var v64
	var v65
	var v66
	var v67
	var v68
	var v69
	var v70
	var v71
	var v72
	var v73
	var v74
	var v75
	var v76
	var v77
	var v78
	var v79
	var v80
	var v81
	var v82
	var v83
	var v84
	var v85
	var v86
	var v87
	var v88
	var v89
	var v90
	var v91
	var v92
	var v93
	var v94
	var v95
	var v96
	var v97
	var v98
	var v99
	var v100
	var v101
	var v102
	var v103
	var v104
	var v105
	var v106
	var v107
	var v108
	var v109
	var v110
	var v111
	var v112
	var v113
	var v114
	var v115
	var v116
	var v117
	var v118
	var v119
	var v120
	var v121
	var v122
	var v123
	var v124
	var v125
	var v126
	var v127
	var v128
	var v129
	var v130
	var v131
	var v132
	var v133
	var v134
	var v135
	var v136
	var v137
	var v138
	var v139
	var v140
	var v141
	var v142
	var v143
	var v144
	var v145
	var v146
	var v147
	var v148
	var v149
	var v150
	var v151
	var v152
	var v153
	var v154
	var v155
	var v156
	if not (e.ossos): # IL_0012
		return # IL_0017
	if not (e.ossos.size()): # IL_0023
		return # IL_0028
	if not (e.ligado): # IL_002f
		return # IL_0034
	v0 = Vector3.ONE # IL_003a
	v1 = e.ossos["cf_n_height"] # IL_0047
	if (v1 != null): # IL_004e
		v0 = v1.escala_local # IL_0059
	if e.habilitados.get("ShoulderL",true): # IL_0060
		v2 = e.ossos["cf_j_arm00_L"] # IL_0072
		v3 = e.ossos["cf_d_shoulder02_L"] # IL_0080
		v4 = e.ossos["cf_j_forearm01_L"] # IL_008d
		v5 = e.ossos["n_goal_forearm_L"] # IL_009c
		if (v2 != null): # IL_00a4
			if (v3 != null): # IL_00af
				if (v5 != null): # IL_00bb
					if (v4 != null): # IL_00c7
						v6 = v5.inverter_ponto(v4.posicao) # IL_00da
						v7 = absf(v6.y) # IL_00e8
						v8 = absf(v6.z) # IL_00f6
						v9 = 0.0 # IL_00fd
						if v7 <= 0.30000001192092896: # IL_0106
							v9 = ((0.30000001192092896-v7)*250.0) # IL_0119
							v10 = v2.posicao_local # IL_0122
							v3.definir_eixo("posicao_local",0,((v10.x-((0.30000001192092896-v7)*0.029999999329447746))-(v8*0.029999999329447746))) # IL_0143
							v3.definir_eixo("posicao_local",1,((0.30000001192092896-v7)*0.20000000298023224)) # IL_0157
						else: # IL_0106
							v9 = 0.0 # IL_0166
							v11 = v2.posicao_local # IL_016f
							v3.definir_eixo("posicao_local",0,(v11.x-(v8*0.029999999329447746))) # IL_0181
							v3.definir_eixo("posicao_local",1,0.0) # IL_018c
						v12 = e.euler(3,v3.rotacao_local) # IL_019d
						v12.y = (v6.z*50.0) # IL_01ae
						v12.z = minf(0.0,(-v9)) # IL_01c2
						v13 = e.quaternion(3,Vector3(v12.x,v12.y,v12.z)) # IL_01e2
						v3.rotacao_local = v13 # IL_01e7
						v3.definir_eixo("posicao_local",2,((-v6.z)*0.05999999865889549)) # IL_01fb
	if e.habilitados.get("ShoulderR",true): # IL_0206
		v14 = e.ossos["cf_j_arm00_R"] # IL_0218
		v15 = e.ossos["cf_d_shoulder02_R"] # IL_0227
		v16 = e.ossos["cf_j_forearm01_R"] # IL_0235
		v17 = e.ossos["n_goal_forearm_R"] # IL_0244
		if (v14 != null): # IL_024d
			if (v15 != null): # IL_0259
				if (v17 != null): # IL_0265
					if (v16 != null): # IL_0271
						v18 = v17.inverter_ponto(v16.posicao) # IL_0284
						v19 = absf(v18.y) # IL_0292
						v20 = absf(v18.z) # IL_02a0
						v21 = 0.0 # IL_02a7
						if v19 <= 0.30000001192092896: # IL_02b0
							v21 = ((0.30000001192092896-v19)*-250.0) # IL_02c3
							v22 = v14.posicao_local # IL_02ce
							v15.definir_eixo("posicao_local",0,((v22.x+((0.30000001192092896-v19)*0.029999999329447746))+(v20*0.029999999329447746))) # IL_02ef
							v15.definir_eixo("posicao_local",1,((0.30000001192092896-v19)*0.20000000298023224)) # IL_0304
						else: # IL_02b0
							v21 = 0.0 # IL_0313
							v23 = v14.posicao_local # IL_031e
							v15.definir_eixo("posicao_local",0,(v23.x+(v20*0.029999999329447746))) # IL_0330
							v15.definir_eixo("posicao_local",1,0.0) # IL_033c
						v24 = e.euler(3,v15.rotacao_local) # IL_034e
						v24.y = ((-v18.z)*50.0) # IL_0360
						v24.z = maxf(0.0,(-v21)) # IL_0374
						v25 = e.quaternion(3,Vector3(v24.x,v24.y,v24.z)) # IL_0394
						v15.rotacao_local = v25 # IL_039a
						v15.definir_eixo("posicao_local",2,((-v18.z)*0.05999999865889549)) # IL_03af
	if e.habilitados.get("UpperarmL",true): # IL_03ba
		v26 = e.ossos["cf_j_arm00_L"] # IL_03cc
		if (v26 != null): # IL_03d5
			v27 = e.euler(5,v26.rotacao_local) # IL_03e7
			v28 = v27.x # IL_03f0
			v29 = e.ossos["cf_d_arm01_L"] # IL_03ff
			if (v29 != null): # IL_0408
				v27 = e.euler(5,v29.rotacao_local) # IL_041a
				v27.x = ((-v28)*0.6000000238418579) # IL_0427
				v30 = e.quaternion(5,Vector3(v27.x,v27.y,v27.z)) # IL_0447
				v29.rotacao_local = v30 # IL_044d
			v29 = e.ossos["cf_d_arm02_L"] # IL_045f
			if (v29 != null): # IL_0468
				v27 = e.euler(5,v29.rotacao_local) # IL_047a
				v27.x = ((-v28)*0.5) # IL_0487
				v31 = e.quaternion(5,Vector3(v27.x,v27.y,v27.z)) # IL_04a7
				v29.rotacao_local = v31 # IL_04ad
			v29 = e.ossos["cf_d_arm03_L"] # IL_04bf
			if (v29 != null): # IL_04c8
				v27 = e.euler(5,v29.rotacao_local) # IL_04da
				v27.x = ((-v28)*0.125) # IL_04e7
				v32 = e.quaternion(5,Vector3(v27.x,v27.y,v27.z)) # IL_0507
				v29.rotacao_local = v32 # IL_050d
	if e.habilitados.get("UpperarmR",true): # IL_0518
		v33 = e.ossos["cf_j_arm00_R"] # IL_052a
		if (v33 != null): # IL_0533
			v34 = e.euler(5,v33.rotacao_local) # IL_0545
			v35 = v34.x # IL_054e
			v36 = e.ossos["cf_d_arm01_R"] # IL_055d
			if (v36 != null): # IL_0566
				v34 = e.euler(5,v36.rotacao_local) # IL_0578
				v34.x = ((-v35)*0.6000000238418579) # IL_0585
				v37 = e.quaternion(5,Vector3(v34.x,v34.y,v34.z)) # IL_05a5
				v36.rotacao_local = v37 # IL_05ab
			v36 = e.ossos["cf_d_arm02_R"] # IL_05bd
			if (v36 != null): # IL_05c6
				v34 = e.euler(5,v36.rotacao_local) # IL_05d8
				v34.x = ((-v35)*0.5) # IL_05e5
				v38 = e.quaternion(5,Vector3(v34.x,v34.y,v34.z)) # IL_0605
				v36.rotacao_local = v38 # IL_060b
			v36 = e.ossos["cf_d_arm03_R"] # IL_061d
			if (v36 != null): # IL_0626
				v34 = e.euler(5,v36.rotacao_local) # IL_0638
				v34.x = ((-v35)*0.125) # IL_0645
				v39 = e.quaternion(5,Vector3(v34.x,v34.y,v34.z)) # IL_0665
				v36.rotacao_local = v39 # IL_066b
	if e.habilitados.get("ElboL",true): # IL_0676
		v40 = e.ossos["cf_j_forearm01_L"] # IL_0687
		if (v40 != null): # IL_0690
			v41 = e.euler(4,v40.rotacao_local) # IL_06a2
			v42 = v41.y # IL_06ab
			v43 = e.ossos["cf_s_elbo_L"] # IL_06b9
			if (v43 != null): # IL_06c2
				v41 = e.euler(4,v43.rotacao_local) # IL_06d4
				v41.y = ((-v42)*0.5) # IL_06e1
				v44 = e.quaternion(4,Vector3(v41.x,v41.y,v41.z)) # IL_0701
				v43.rotacao_local = v44 # IL_0707
				v43.definir_eixo("posicao_local",0,((sin((v42*0.014999999664723873))*0.2199999988079071)*0.10000000149011612)) # IL_0727
				v43.definir_eixo("posicao_local",2,((-0.25+(sin(((v42-1.0)*0.006000000052154064))*0.18000000715255737))*0.10000000149011612)) # IL_0753
			v43 = e.ossos["cf_s_elboback_L"] # IL_0764
			if (v43 != null): # IL_076d
				v41 = e.euler(4,v43.rotacao_local) # IL_077f
				v41.y = ((-v42)*0.5) # IL_078c
				v45 = e.quaternion(4,Vector3(v41.x,v41.y,v41.z)) # IL_07ac
				v43.rotacao_local = v45 # IL_07b2
				v43.definir_eixo("posicao_local",0,(((-tan((v42*0.0038999998942017555)))*12.0)*0.10000000149011612)) # IL_07d3
				v43.definir_eixo("posicao_local",2,(((0.30000001192092896-(sin(((-v42)*0.008999999612569809))*7.599999904632568))-(tan((v42*0.002199999988079071))*16.0))*0.10000000149011612)) # IL_080e
	if e.habilitados.get("ElboR",true): # IL_0819
		v46 = e.ossos["cf_j_forearm01_R"] # IL_082a
		if (v46 != null): # IL_0833
			v47 = e.euler(4,v46.rotacao_local) # IL_0845
			v48 = v47.y # IL_084e
			v49 = e.ossos["cf_s_elbo_R"] # IL_085c
			if (v49 != null): # IL_0865
				v47 = e.euler(4,v49.rotacao_local) # IL_0877
				v47.y = ((-v48)*0.5) # IL_0884
				v50 = e.quaternion(4,Vector3(v47.x,v47.y,v47.z)) # IL_08a4
				v49.rotacao_local = v50 # IL_08aa
				v49.definir_eixo("posicao_local",0,((sin((v48*0.014999999664723873))*0.2199999988079071)*0.10000000149011612)) # IL_08ca
				v49.definir_eixo("posicao_local",2,((-0.25-(sin(((v48-1.0)*0.006000000052154064))*0.18000000715255737))*0.10000000149011612)) # IL_08f6
			v49 = e.ossos["cf_s_elboback_R"] # IL_0907
			if (v49 != null): # IL_0910
				v47 = e.euler(4,v49.rotacao_local) # IL_0922
				v47.y = ((-v48)*0.5) # IL_092f
				v51 = e.quaternion(4,Vector3(v47.x,v47.y,v47.z)) # IL_094f
				v49.rotacao_local = v51 # IL_0955
				v49.definir_eixo("posicao_local",0,(((-tan((v48*0.0038999998942017555)))*12.0)*0.10000000149011612)) # IL_0976
				v49.definir_eixo("posicao_local",2,(((0.30000001192092896-(sin((v48*0.008999999612569809))*7.599999904632568))+(tan((v48*0.002199999988079071))*16.0))*0.10000000149011612)) # IL_09b0
	if e.habilitados.get("ForearmL",true): # IL_09bb
		v52 = e.ossos["cf_j_forearm01_L"] # IL_09cc
		v53 = e.ossos["cf_j_hand_L"] # IL_09db
		v54 = e.ossos["cf_j_middle01_L"] # IL_09ea
		if (v52 != null): # IL_09f3
			if (v53 != null): # IL_09ff
				if (v54 != null): # IL_0a0b
					e.calculo.escala_local = Vector3.ONE # IL_0a1b
					e.calculo.posicao = v53.posicao # IL_0a2d
					e.calculo.rotacao = v52.rotacao # IL_0a3f
					v55 = e.calculo.inverter_ponto(v54.posicao) # IL_0a56
					v55.y = maxf(0.0,v55.y) # IL_0a6b
					v56 = ((v55.y*100.0)*0.01745329238474369) # IL_0a83
					v57 = e.ossos["cf_d_hand_L"] # IL_0a92
					if (v57 != null): # IL_0a9b
						v57.definir_eixo("posicao_local",0,((-(0.25-(sin(v56)*15.0)))*0.10000000149011612)) # IL_0abc
						v57.definir_eixo("posicao_local",1,((sin(v56)*15.0)*0.10000000149011612)) # IL_0ad6
					e.calculo.posicao = v53.posicao # IL_0ae8
					e.calculo.rotacao = v53.rotacao # IL_0afa
					e.calculo.escala_local = v53.escala_local # IL_0b0c
					e.calculo.transladar(Vector3(-0.009999999776482582,0.009999999776482582,0.0)) # IL_0b27
					v55 = e.calculo.posicao # IL_0b37
					v55 = v52.inverter_ponto(v55) # IL_0b42
					v55.x = 0.0 # IL_0b4b
					v55 = v55.normalized() # IL_0b57
					v58 = (e.angulo(Vector3.UP,v55)*e.sinal(v55.z)) # IL_0b72
					v57 = e.ossos["cf_d_wrist_L"] # IL_0b81
					if (v57 != null): # IL_0b8a
						v57.definir_rotacao_x(v58) # IL_0b93
	if e.habilitados.get("ForearmR",true): # IL_0b9e
		v59 = e.ossos["cf_j_forearm01_R"] # IL_0baf
		v60 = e.ossos["cf_j_hand_R"] # IL_0bbe
		v61 = e.ossos["cf_j_middle01_R"] # IL_0bcd
		if (v59 != null): # IL_0bd6
			if (v60 != null): # IL_0be2
				if (v61 != null): # IL_0bee
					e.calculo.escala_local = Vector3.ONE # IL_0bfe
					e.calculo.posicao = v60.posicao # IL_0c10
					e.calculo.rotacao = v59.rotacao # IL_0c22
					v62 = e.calculo.inverter_ponto(v61.posicao) # IL_0c39
					v62.y = maxf(0.0,v62.y) # IL_0c4e
					v63 = ((v62.y*100.0)*0.01745329238474369) # IL_0c66
					v64 = e.ossos["cf_d_hand_R"] # IL_0c75
					if (v64 != null): # IL_0c7e
						v64.definir_eixo("posicao_local",0,((-(-0.25+(sin(v63)*15.0)))*0.10000000149011612)) # IL_0c9f
						v64.definir_eixo("posicao_local",1,((sin(v63)*15.0)*0.10000000149011612)) # IL_0cb9
					e.calculo.posicao = v60.posicao # IL_0ccb
					e.calculo.rotacao = v60.rotacao # IL_0cdd
					e.calculo.escala_local = v60.escala_local # IL_0cef
					e.calculo.transladar(Vector3(0.009999999776482582,0.009999999776482582,0.0)) # IL_0d0a
					v62 = e.calculo.posicao # IL_0d1a
					v62 = v59.inverter_ponto(v62) # IL_0d25
					v62.x = 0.0 # IL_0d2e
					v62 = v62.normalized() # IL_0d3a
					v65 = (e.angulo(Vector3.UP,v62)*e.sinal(v62.z)) # IL_0d55
					v64 = e.ossos["cf_d_wrist_R"] # IL_0d64
					if (v64 != null): # IL_0d6d
						v64.definir_rotacao_x(v65) # IL_0d76
	if e.habilitados.get("HandL",true): # IL_0d81
		v66 = e.ossos["cf_j_hand_L"] # IL_0d93
		if (v66 != null): # IL_0d9c
			v67 = e.euler(5,v66.rotacao_local) # IL_0dae
			v68 = v67.x # IL_0db7
			v69 = e.ossos["cf_d_forearm02_L"] # IL_0dc6
			if (v69 != null): # IL_0dcf
				v67 = e.euler(5,v69.rotacao_local) # IL_0de1
				v67.x = (v68*0.44999998807907104) # IL_0ded
				v70 = e.quaternion(5,Vector3(v67.x,v67.y,v67.z)) # IL_0e0d
				v69.rotacao_local = v70 # IL_0e13
	if e.habilitados.get("HandR",true): # IL_0e1e
		v71 = e.ossos["cf_j_hand_R"] # IL_0e30
		if (v71 != null): # IL_0e39
			v72 = e.euler(5,v71.rotacao_local) # IL_0e4b
			v73 = v72.x # IL_0e54
			v74 = e.ossos["cf_d_forearm02_R"] # IL_0e63
			if (v74 != null): # IL_0e6c
				v72 = e.euler(5,v74.rotacao_local) # IL_0e7e
				v72.x = (v73*0.44999998807907104) # IL_0e8a
				v75 = e.quaternion(5,Vector3(v72.x,v72.y,v72.z)) # IL_0eaa
				v74.rotacao_local = v75 # IL_0eb0
	if e.habilitados.get("LegL",true): # IL_0ebb
		v76 = 0.0 # IL_0ec5
		v77 = e.ossos["cf_j_waist02"] # IL_0ed3
		v78 = e.ossos["cf_j_thigh00_L"] # IL_0ee2
		v79 = e.ossos["cf_j_leg01_L"] # IL_0ef1
		if (v77 != null): # IL_0efa
			if (v78 != null): # IL_0f06
				if (v79 != null): # IL_0f12
					e.calculo.escala_local = Vector3.ONE # IL_0f22
					e.calculo.posicao = v78.posicao # IL_0f34
					e.calculo.rotacao = v77.rotacao # IL_0f46
					v80 = ((e.calculo.inverter_ponto(v79.posicao)/v0.y)*10.0) # IL_0f73
					if 0.0 <= v80.y: # IL_0f81
						v76 = absf(v80.y) # IL_0f92
					v77 = e.ossos["n_leg_goal_L"] # IL_0fa1
					v78 = e.ossos["cf_j_leg01_L"] # IL_0fb0
					if (v77 != null): # IL_0fb9
						if (v78 != null): # IL_0fc5
							v80 = (v77.inverter_ponto(v78.posicao)*-10.0) # IL_0fe2
							v81 = e.ossos["cf_s_leg_L"] # IL_0ff1
							if (v81 != null): # IL_0ffa
								v81.definir_eixo("posicao_local",0,(((1.0+(v80.x*0.20000000298023224))+((absf((v80.z*1.100000023841858))-(8.848999977111816-v80.y))*0.05999999865889549))*-0.10000000149011612)) # IL_1041
								v81.definir_eixo("posicao_local",1,((((1.0+((8.848999977111816-v80.y)*0.4000000059604645))+(v80.x*0.20000000298023224))+(v76*0.6000000238418579))*0.10000000149011612)) # IL_107e
								v81.definir_eixo("posicao_local",2,(((((-v80.z)*0.20000000298023224)+(v80.x*0.05000000074505806))-(v76*0.4000000059604645))*0.10000000149011612)) # IL_10b0
								v82 = (((v80.z*6.0)-(v80.x*2.0))-(v76*5.0)) # IL_10d9
								v83 = (((-v80.x)*12.0)-(v80.z*3.0)) # IL_10f7
								v84 = (-v80.x) # IL_1101
								v85 = e.quaternion(5,Vector3(v82,v83,v84)) # IL_110f
								v81.rotacao_local = v85 # IL_1115
								v81.definir_eixo("escala_local",0,(1.0+(absf(v80.z)*0.20000000298023224))) # IL_1134
								v81.definir_eixo("escala_local",1,(1.0+(v76*0.4000000059604645))) # IL_1149
								v81.definir_eixo("escala_local",2,((1.0+(absf(v80.z)*0.30000001192092896))+(v76*0.30000001192092896))) # IL_1171
							v81 = e.ossos["cf_d_siri_L"] # IL_1183
							if (v81 != null): # IL_118c
								v81.definir_eixo("posicao_local",0,((((-0.699999988079071+(v80.x*0.009999999776482582))-absf((v80.x*0.019999999552965164)))-absf((v80.z*0.004999999888241291)))*0.10000000149011612)) # IL_11d2
								v81.definir_eixo("posicao_local",1,(((((8.848999977111816-v80.y)*0.009999999776482582)+absf((v80.z*0.019999999552965164)))+(v80.x*0.03999999910593033))*0.10000000149011612)) # IL_1213
								v81.definir_eixo("posicao_local",2,(((((-(8.848999977111816-v80.y))*0.029999999329447746)-((v80.z-(v76*3.0))*0.029999999329447746))-(absf(v80.x)*0.019999999552965164))*0.10000000149011612)) # IL_125e
								v86 = ((((v80.z*4.0)-((8.848999977111816-v80.y)*4.0))-(v80.x*2.0))-(v76*3.0)) # IL_129b
								v87 = (((-v80.x)*6.0)-(v76*4.0)) # IL_12b4
								v88 = ((-v80.x)*6.0) # IL_12c4
								v89 = e.quaternion(5,Vector3(v86,v87,v88)) # IL_12d2
								v81.definir_eixo("escala_local",0,(1.0+(absf(v80.z)*0.019999999552965164))) # IL_12ee
								v81.definir_eixo("escala_local",1,(1.0+(absf(v76)*0.009999999776482582))) # IL_1308
	if e.habilitados.get("LegR",true): # IL_1313
		v90 = 0.0 # IL_131d
		v91 = e.ossos["cf_j_waist02"] # IL_132b
		v92 = e.ossos["cf_j_thigh00_R"] # IL_133a
		v93 = e.ossos["cf_j_leg01_R"] # IL_1349
		if (v91 != null): # IL_1352
			if (v92 != null): # IL_135e
				if (v93 != null): # IL_136a
					e.calculo.escala_local = Vector3.ONE # IL_137a
					e.calculo.posicao = v92.posicao # IL_138c
					e.calculo.rotacao = v91.rotacao # IL_139e
					if (v91 != null): # IL_13aa
						if (v92 != null): # IL_13b6
							v94 = ((e.calculo.inverter_ponto(v93.posicao)/v0.y)*10.0) # IL_13e3
							if 0.0 <= v94.y: # IL_13f1
								v90 = absf(v94.y) # IL_1402
							v91 = e.ossos["n_leg_goal_R"] # IL_1411
							v92 = e.ossos["cf_j_leg01_R"] # IL_1420
							v94 = (v91.inverter_ponto(v92.posicao)*-10.0) # IL_143a
							v95 = e.ossos["cf_s_leg_R"] # IL_1449
							if (v95 != null): # IL_1452
								v95.definir_eixo("posicao_local",0,(((-1.0+(v94.x*0.20000000298023224))-((absf((v94.z*1.100000023841858))-(8.848999977111816-v94.y))*0.05999999865889549))*-0.10000000149011612)) # IL_1499
								v95.definir_eixo("posicao_local",1,((((1.0+((8.848999977111816-v94.y)*0.4000000059604645))-(v94.x*0.20000000298023224))+(v90*0.6000000238418579))*0.10000000149011612)) # IL_14d6
								v95.definir_eixo("posicao_local",2,(((((-v94.z)*0.20000000298023224)-(v94.x*0.05000000074505806))-(v90*0.4000000059604645))*0.10000000149011612)) # IL_1508
								v96 = (((v94.z*6.0)+(v94.x*2.0))-(v90*5.0)) # IL_1531
								v97 = (((-v94.x)*12.0)+(v94.z*3.0)) # IL_154f
								v98 = (-v94.x) # IL_1559
								v99 = e.quaternion(5,Vector3(v96,v97,v98)) # IL_1567
								v95.rotacao_local = v99 # IL_156d
								v95.definir_eixo("escala_local",0,(1.0+(absf(v94.z)*0.20000000298023224))) # IL_158c
								v95.definir_eixo("escala_local",1,(1.0+(v90*0.4000000059604645))) # IL_15a1
								v95.definir_eixo("escala_local",2,((1.0+(absf(v94.z)*0.30000001192092896))+(v90*0.30000001192092896))) # IL_15c9
							v95 = e.ossos["cf_d_siri_R"] # IL_15db
							if (v95 != null): # IL_15e4
								v95.definir_eixo("posicao_local",0,((((0.699999988079071+(v94.x*0.009999999776482582))+absf((v94.x*0.019999999552965164)))+absf((v94.z*0.004999999888241291)))*0.10000000149011612)) # IL_162a
								v95.definir_eixo("posicao_local",1,(((((8.848999977111816-v94.y)*0.009999999776482582)+absf((v94.z*0.019999999552965164)))-(v94.x*0.03999999910593033))*0.10000000149011612)) # IL_166b
								v95.definir_eixo("posicao_local",2,(((((-(8.848999977111816-v94.y))*0.029999999329447746)-((v94.z-(v90*3.0))*0.029999999329447746))-(absf(v94.x)*0.019999999552965164))*0.10000000149011612)) # IL_16b6
								v100 = ((((v94.z*4.0)-((8.848999977111816-v94.y)*4.0))+(v94.x*2.0))-(v90*3.0)) # IL_16f3
								v101 = (((-v94.x)*6.0)+(v90*4.0)) # IL_170c
								v102 = ((-v94.x)*6.0) # IL_171c
								v103 = e.quaternion(5,Vector3(v100,v101,v102)) # IL_172a
								v95.definir_eixo("escala_local",0,(1.0+(absf(v94.z)*0.019999999552965164))) # IL_1746
								v95.definir_eixo("escala_local",1,(1.0+(absf(v90)*0.009999999776482582))) # IL_1760
	if e.habilitados.get("ThighL",true): # IL_176b
		v104 = e.ossos["cf_j_thigh00_L"] # IL_177d
		if (null!=v104): # IL_1787
			v105 = e.euler(5,v104.rotacao_local) # IL_1799
			v106 = v105.y # IL_17a2
			v107 = e.ossos["cf_d_thigh01_L"] # IL_17b1
			v105 = e.euler(5,v107.rotacao_local) # IL_17c0
			v105.y = ((-v106)*0.75) # IL_17cd
			v108 = e.quaternion(5,Vector3(v105.x,v105.y,v105.z)) # IL_17ed
			v107.rotacao_local = v108 # IL_17f3
			v107 = e.ossos["cf_d_thigh02_L"] # IL_1805
			v105 = e.euler(5,v107.rotacao_local) # IL_1814
			v105.y = ((-v106)*0.5) # IL_1821
			v108 = e.quaternion(5,Vector3(v105.x,v105.y,v105.z)) # IL_1841
			v107.rotacao_local = v108 # IL_1847
			v107 = e.ossos["cf_d_thigh03_L"] # IL_1859
			v105 = e.euler(5,v107.rotacao_local) # IL_1868
			v105.y = ((-v106)*0.25) # IL_1875
			v108 = e.quaternion(5,Vector3(v105.x,v105.y,v105.z)) # IL_1895
			v107.rotacao_local = v108 # IL_189b
	if e.habilitados.get("ThighR",true): # IL_18a6
		v109 = e.ossos["cf_j_thigh00_R"] # IL_18b8
		if (null!=v109): # IL_18c2
			v110 = e.euler(5,v109.rotacao_local) # IL_18d4
			v111 = v110.y # IL_18dd
			v112 = e.ossos["cf_d_thigh01_R"] # IL_18ec
			v110 = e.euler(5,v112.rotacao_local) # IL_18fb
			v110.y = ((-v111)*0.75) # IL_1908
			v113 = e.quaternion(5,Vector3(v110.x,v110.y,v110.z)) # IL_1928
			v112.rotacao_local = v113 # IL_192e
			v112 = e.ossos["cf_d_thigh02_R"] # IL_1940
			v110 = e.euler(5,v112.rotacao_local) # IL_194f
			v110.y = ((-v111)*0.5) # IL_195c
			v113 = e.quaternion(5,Vector3(v110.x,v110.y,v110.z)) # IL_197c
			v112.rotacao_local = v113 # IL_1982
			v112 = e.ossos["cf_d_thigh03_R"] # IL_1994
			v110 = e.euler(5,v112.rotacao_local) # IL_19a3
			v110.y = ((-v111)*0.25) # IL_19b0
			v113 = e.quaternion(5,Vector3(v110.x,v110.y,v110.z)) # IL_19d0
			v112.rotacao_local = v113 # IL_19d6
	if e.habilitados.get("KneeL",true): # IL_19e1
		v114 = e.ossos["cf_j_leg01_L"] # IL_19f3
		if (v114 != null): # IL_19fc
			v115 = e.euler(5,v114.rotacao_local) # IL_1a0e
			v116 = v115.x # IL_1a17
			v117 = e.ossos["cf_s_kneeB_L"] # IL_1a26
			if (v117 != null): # IL_1a2f
				v115 = e.euler(5,v117.rotacao_local) # IL_1a41
				v115.x = ((-v116)*0.5) # IL_1a4e
				v115.z = (v116*0.10000000149011612) # IL_1a5d
				v118 = e.quaternion(5,Vector3(v115.x,v115.y,v115.z)) # IL_1a7d
				v117.rotacao_local = v118 # IL_1a83
				v117.definir_eixo("posicao_local",1,(((-(v116*0.04800000041723251))+(sin((v116*0.009999999776482582))*1.100000023841858))*0.10000000149011612)) # IL_1aad
				v117.definir_eixo("posicao_local",2,(((-0.6000000238418579-(sin((v116*0.011500000022351742))*4.0))+(tan((v116*0.0031999999191612005))*5.0))*0.10000000149011612)) # IL_1ae7
			v117 = e.ossos["cf_d_kneeF_L"] # IL_1af8
			if (v117 != null): # IL_1b01
				v115 = e.euler(5,v117.rotacao_local) # IL_1b13
				v115.x = ((-v116)*0.5) # IL_1b20
				v119 = e.quaternion(5,Vector3(v115.x,v115.y,v115.z)) # IL_1b40
				v117.rotacao_local = v119 # IL_1b46
				v117.definir_eixo("posicao_local",1,(((sin((v116*0.012000000104308128))*1.7999999523162842)-(tan((v116*0.0033499998971819878))*4.5))*0.10000000149011612)) # IL_1b7a
				v117.definir_eixo("posicao_local",2,(((0.4000000059604645+(v116*0.012500000186264515))-(tan((v116*0.0031999999191612005))*4.5))*0.10000000149011612)) # IL_1ba9
	if e.habilitados.get("KneeR",true): # IL_1bb4
		v120 = e.ossos["cf_j_leg01_R"] # IL_1bc6
		if (v120 != null): # IL_1bcf
			v121 = e.euler(5,v120.rotacao_local) # IL_1be1
			v122 = v121.x # IL_1bea
			v123 = e.ossos["cf_s_kneeB_R"] # IL_1bf9
			if (v123 != null): # IL_1c02
				v121 = e.euler(5,v123.rotacao_local) # IL_1c14
				v121.x = ((-v122)*0.5) # IL_1c21
				v121.z = ((-v122)*0.10000000149011612) # IL_1c31
				v124 = e.quaternion(5,Vector3(v121.x,v121.y,v121.z)) # IL_1c51
				v123.rotacao_local = v124 # IL_1c57
				v123.definir_eixo("posicao_local",1,(((-(v122*0.04800000041723251))+(sin((v122*0.009999999776482582))*1.100000023841858))*0.10000000149011612)) # IL_1c81
				v123.definir_eixo("posicao_local",2,(((-0.6000000238418579-(sin((v122*0.011500000022351742))*4.0))+(tan((v122*0.0031999999191612005))*5.0))*0.10000000149011612)) # IL_1cbb
			v123 = e.ossos["cf_d_kneeF_R"] # IL_1ccd
			if (v123 != null): # IL_1cd6
				v121 = e.euler(5,v123.rotacao_local) # IL_1ce8
				v121.x = ((-v122)*0.5) # IL_1cf5
				v125 = e.quaternion(5,Vector3(v121.x,v121.y,v121.z)) # IL_1d15
				v123.rotacao_local = v125 # IL_1d1b
				v123.definir_eixo("posicao_local",1,(((sin((v122*0.012000000104308128))*1.7999999523162842)-(tan((v122*0.0033499998971819878))*4.5))*0.10000000149011612)) # IL_1d4f
				v123.definir_eixo("posicao_local",2,(((0.4000000059604645+(v122*0.012500000186264515))-(tan((v122*0.0031999999191612005))*4.5))*0.10000000149011612)) # IL_1d7e
	if e.habilitados.get("CalfL",true): # IL_1d89
		v126 = e.ossos["cf_j_leg03_L"] # IL_1d9b
		if (v126 != null): # IL_1da4
			v127 = e.euler(5,v126.rotacao_local) # IL_1db6
			v128 = v127.y # IL_1dbf
			v129 = e.ossos["cf_d_leg02_L"] # IL_1dce
			if (v129 != null): # IL_1dd7
				v127 = e.euler(5,v129.rotacao_local) # IL_1de9
				v127.y = (v128*0.5) # IL_1df5
				v130 = e.quaternion(5,Vector3(v127.x,v127.y,v127.z)) # IL_1e15
				v129.rotacao_local = v130 # IL_1e1b
	if e.habilitados.get("CalfR",true): # IL_1e26
		v131 = e.ossos["cf_j_leg03_R"] # IL_1e38
		if (v131 != null): # IL_1e41
			v132 = e.euler(5,v131.rotacao_local) # IL_1e53
			v133 = v132.y # IL_1e5c
			v134 = e.ossos["cf_d_leg02_R"] # IL_1e6b
			if (v134 != null): # IL_1e74
				v132 = e.euler(5,v134.rotacao_local) # IL_1e86
				v132.y = (v133*0.5) # IL_1e92
				v135 = e.quaternion(5,Vector3(v132.x,v132.y,v132.z)) # IL_1eb2
				v134.rotacao_local = v135 # IL_1eb8
	if e.habilitados.get("Bust",true): # IL_1ec3
		v136 = e.ossos["cf_j_spine03"] # IL_1ed5
		v137 = e.ossos["cf_d_bust00"] # IL_1ee4
		if (v136 != null): # IL_1eed
			if (v137 != null): # IL_1ef9
				v138 = e.euler(5,v136.rotacao_local) # IL_1f0b
				v139 = e.quaternion(5,Vector3(((-v138.x)*0.3499999940395355),((-v138.y)*0.3499999940395355),((-v138.z)*0.3499999940395355))) # IL_1f3d
				v137.rotacao_local = v139 # IL_1f43
				v137.definir_eixo("posicao_local",1,((-0.08100000023841858+(v138.x*0.003000000026077032))*0.10000000149011612)) # IL_1f63
				v137.definir_eixo("posicao_local",2,((v138.x*0.004000000189989805)*0.10000000149011612)) # IL_1f7d
	if e.habilitados.get("BustColDB",true): # IL_1f88
		v140 = e.ossos["cf_j_bust02_L"] # IL_1f9a
		v141 = e.ossos["cf_d_hit_bust_L"] # IL_1fa9
		if (v140 != null): # IL_1fb2
			if (v141 != null): # IL_1fbe
				v142 = v140.posicao_local # IL_1fcc
				v143 = v140.posicao_local # IL_1fe3
				v144 = v140.posicao_local # IL_1ffa
				v141.posicao_local = Vector3(((-v142.x)*0.5),((-v143.y)*0.5),((-v144.z)*0.25)) # IL_200a
				v145 = v140.escala_local # IL_201d
				v146 = v140.escala_local # IL_2039
				v147 = v140.escala_local # IL_2055
				v141.escala_local = Vector3((1.5-(v145.x*0.5)),(1.5-(v146.y*0.5)),(1.5-(v147.z*0.5))) # IL_2065
		v140 = e.ossos["cf_j_bust02_R"] # IL_2077
		v141 = e.ossos["cf_d_hit_bust_R"] # IL_2086
		if (v140 != null): # IL_208f
			if (v141 != null): # IL_209b
				v148 = v140.posicao_local # IL_20a9
				v149 = v140.posicao_local # IL_20c0
				v150 = v140.posicao_local # IL_20d7
				v141.posicao_local = Vector3(((-v148.x)*0.5),((-v149.y)*0.5),((-v150.z)*0.25)) # IL_20e7
				v151 = v140.escala_local # IL_20fa
				v152 = v140.escala_local # IL_2116
				v153 = v140.escala_local # IL_2132
				v141.escala_local = Vector3((1.5-(v151.x*0.5)),(1.5-(v152.y*0.5)),(1.5-(v153.z*0.5))) # IL_2142
	if e.habilitados.get("AcsNull",true): # IL_214d
		v154 = e.ossos["cf_j_head"] # IL_215f
		if (v154 != null): # IL_2168
			v155 = e.euler(5,v154.rotacao_local) # IL_217a
			v156 = e.ossos["a_n_neck"] # IL_2189
			if (v156 != null): # IL_2192
				v156.definir_eixo("posicao_local",0,(v155.z*0.00019999999494757503)) # IL_21a6
				v156.definir_eixo("posicao_local",2,((-0.07999999821186066-(v155.x*0.0020000000949949026))*0.10000000149011612)) # IL_21c6
	return # IL_21cb
