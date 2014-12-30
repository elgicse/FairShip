import ROOT
import shipunit as u
import hnl

def addHNLtoROOT(pid=9900014 ,m = 1.0, g=3.654203020370371E-21):
 pdg = ROOT.TDatabasePDG.Instance()
 pdg.AddParticle('N2','HNL', m, False, g, 0., 'N2', pid)

def configure(P8gen, mass, couplings, inclusive, deepCopy=False):
 # configure pythia8 for Ship usage
 P8gen.UseRandom3() # TRandom1 or TRandom3 ?
 P8gen.SetMom(400)  # beam momentum in GeV 
 if deepCopy: P8gen.UseDeepCopy()
 pdg = ROOT.TDatabasePDG.Instance()
 # pythia stuff not known to ROOT
 pdg.AddParticle('system','system', 0., False, 0., 0., 'XXX', 90)
 pdg.AddParticle('p_diffr+','p_diffr+', 0., False, 0., 0., 'XXX', 9902210)
 # let strange particle decay in Geant4
 ## the following does not work because need to have N2 decaying
 #P8gen.SetParameters("ParticleDecays:limitTau0 = on")
 #P8gen.SetParameters("ParticleDecays:tau0Max = 1")
 # explicitly make KS and KL stable
 P8gen.SetParameters("130:mayDecay  = off")
 P8gen.SetParameters("310:mayDecay  = off")
 P8gen.SetParameters("3122:mayDecay = off")
 if inclusive:
  P8gen.SetParameters("SoftQCD:inelastic = on")
  P8gen.SetParameters("PhotonCollision:gmgm2mumu = on")
  P8gen.SetParameters("PromptPhoton:all = on")
  P8gen.SetParameters("WeakBosonExchange:all = on")
 else:
  P8gen.SetParameters("HardQCD::hardccbar  = on")
  # add HNL
  #ctau = 5.4E+06 # for tests use 5.4E+03  # nominal ctau = 54 km = 5.4E+06 cm = 5.4E+07 mm
  #mass = 1.0 # GeV
  hnl_instance = hnl.HNL(mass, couplings, debug=True)
  ctau = hnl_instance.computeNLifetime(system="FairShip") * u.c_light * u.cm
  P8gen.SetParameters("9900014:new = N2 N2 2 0 0 "+str(mass)+" 0.0 0.0 0.0 "+str(ctau/u.mm)+"  0   1   0   1   0")  
  P8gen.SetParameters("9900014:isResonance = false")
  # Adding decay modes...
  # N -> pi e
  width = hnl_instance.findBranchingRatio('N -> pi e')
  P8gen.SetParameters("9900014:addChannel =  1  "+str(width/2.)"  0 -11  -211")
  P8gen.SetParameters("9900014:addChannel =  1  "+str(width/2.)"  0  11   211")
  # N -> pi mu
  width = hnl_instance.findBranchingRatio('N -> pi mu')
  P8gen.SetParameters("9900014:addChannel =  1  "+str(width/2.)"  0 -13  -211")
  P8gen.SetParameters("9900014:addChannel =  1  "+str(width/2.)"  0  13   211")
  # N -> rho e
  width = hnl_instance.findBranchingRatio('N -> rho e')
  P8gen.SetParameters("9900014:addChannel =  1  "+str(width/2.)"  0 -11  -213")
  P8gen.SetParameters("9900014:addChannel =  1  "+str(width/2.)"  0  11   213")
  # N -> rho mu
  width = hnl_instance.findBranchingRatio('N -> rho mu')
  P8gen.SetParameters("9900014:addChannel =  1  "+str(width/2.)"  0 -13  -213")
  P8gen.SetParameters("9900014:addChannel =  1  "+str(width/2.)"  0  13   213")
  # Finish HNL setup...
  P8gen.SetParameters("9900014:mayDecay = on")
  P8gen.SetHNLId(9900014)
  # also add to PDG
  gamma = u.hbarc / float(ctau) #197.3269631e-16 / float(ctau) # hbar*c = 197 MeV*fm = 197e-16 GeV*cm
  #pdg.AddParticle('N2','HNL', float(mass), False, gamma, 0., 'N2', 9900014)
  addHNLtoROOT(pid=9900014,m=mass,g=gamma)
  # 12 14 16 neutrinos replace with N2
  # overwrite /\c decays
  P8gen.SetParameters("4122:new  Lambda_c+   Lambda_cbar-   2   3   0    2.28646    0.00000    0.00000    0.00000  5.99000e-02   0   1   0   1   0")
  P8gen.SetParameters("4122:addChannel = 1   0.0030000   22      -11       9900014     2112")  
  P8gen.SetParameters("4122:addChannel = 1   0.0020000   22      -11       9900014     2114")  
  P8gen.SetParameters("4122:addChannel = 1   0.0180000   22      -11       9900014     3122")  
  P8gen.SetParameters("4122:addChannel = 1   0.0050000   22      -11       9900014     3212")  
  P8gen.SetParameters("4122:addChannel = 1   0.0050000   22      -11       9900014     3214")  
  P8gen.SetParameters("4122:addChannel = 1   0.0030000   22      -13       9900014     2112")  
  P8gen.SetParameters("4122:addChannel = 1   0.0020000   22      -13       9900014     2114")  
  P8gen.SetParameters("4122:addChannel = 1   0.0180000   22      -13       9900014     3122")  
  P8gen.SetParameters("4122:addChannel = 1   0.0050000   22      -13       9900014     3212")  
  P8gen.SetParameters("4122:addChannel = 1   0.0050000   22      -13       9900014     3214 ") 
  P8gen.SetParameters("4122:addChannel = 1   0.0060000   22      -11       9900014     2112      111")  
  P8gen.SetParameters("4122:addChannel = 1   0.0060000   22      -11       9900014     2212     -211") 
  P8gen.SetParameters("4122:addChannel = 1   0.0060000   22      -13       9900014     2112      111 ") 
  P8gen.SetParameters("4122:addChannel = 1   0.0060000   22      -13       9900014     2212     -211 ") 
  # overwrite Ds decays
  P8gen.SetParameters("431:new  D_s+  D_s-  1   3   0    1.96849    0.00000    0.00000    0.00000  1.49900e-01   0   1   0   1   0")
  P8gen.SetParameters("431:addChannel = 1   0.0061600    0      -13       9900014")
  P8gen.SetParameters("431:addChannel = 1   0.0640000    0      -15       9900014")
  P8gen.SetParameters("431:addChannel = 1   0.0307000   22      -11       9900014      221") 
  P8gen.SetParameters("431:addChannel = 1   0.0027000   22      -11       9900014      311") 
  P8gen.SetParameters("431:addChannel = 1   0.0010000   22      -11       9900014     -313") 
  P8gen.SetParameters("431:addChannel = 1   0.0106000   22      -11       9900014      331")
  P8gen.SetParameters("431:addChannel = 1   0.0242000   22      -11       9900014      333") 
  P8gen.SetParameters("431:addChannel = 1   0.0307000   22      -13       9900014      221") 
  P8gen.SetParameters("431:addChannel = 1   0.0027000   22      -13       9900014      311") 
  P8gen.SetParameters("431:addChannel = 1   0.0010000   22      -13       9900014     -313")
  P8gen.SetParameters("431:addChannel = 1   0.0106000   22      -13       9900014      331") 
  P8gen.SetParameters("431:addChannel = 1   0.0242000   22      -13       9900014      333") 
  # overwrite D+ decays
  P8gen.SetParameters("411:new  D+ D-  1   3   0    1.86962    0.00000    0.00000    0.00000  3.11800e-01   0   1   0   1   0")
  P8gen.SetParameters("411:addChannel = 1   0.0004000    0      -13       9900014") 
  P8gen.SetParameters("411:addChannel = 1   0.0010000    0      -15       9900014") 
  P8gen.SetParameters("411:addChannel = 1   0.0043000   22      -11       9900014      111") 
  P8gen.SetParameters("411:addChannel = 1   0.0028000   22      -11       9900014      113")
  P8gen.SetParameters("411:addChannel = 1   0.0026000   22      -11       9900014      221") 
  P8gen.SetParameters("411:addChannel = 1   0.0028000   22      -11       9900014      223") 
  P8gen.SetParameters("411:addChannel = 1   0.0900000   22      -11       9900014      311") 
  P8gen.SetParameters("411:addChannel = 1   0.0554000   22      -11       9900014     -313") 
  P8gen.SetParameters("411:addChannel = 1   0.0038000   22      -11       9900014     -315")
  P8gen.SetParameters("411:addChannel = 1   0.0005000   22      -11       9900014      331")
  P8gen.SetParameters("411:addChannel = 1   0.0036000   22      -11       9900014   -10313") 
  P8gen.SetParameters("411:addChannel = 1   0.0043000   22      -13       9900014      111") 
  P8gen.SetParameters("411:addChannel = 1   0.0028000   22      -13       9900014      113")
  P8gen.SetParameters("411:addChannel = 1   0.0026000   22      -13       9900014      221") 
  P8gen.SetParameters("411:addChannel = 1   0.0028000   22      -13       9900014      223") 
  P8gen.SetParameters("411:addChannel = 1   0.0874000   22      -13       9900014      311") 
  P8gen.SetParameters("411:addChannel = 1   0.0533000   22      -13       9900014     -313") 
  P8gen.SetParameters("411:addChannel = 1   0.0038000   22      -13       9900014     -315") 
  P8gen.SetParameters("411:addChannel = 1   0.0005000   22      -13       9900014      331") 
  P8gen.SetParameters("411:addChannel = 1   0.0036000   22      -13       9900014   -10313") 
  P8gen.SetParameters("411:addChannel = 1   0.0014000   22      -11       9900014      311      111") 
  P8gen.SetParameters("411:addChannel = 1   0.0027000   22      -11       9900014     -321      211") 
  P8gen.SetParameters("411:addChannel = 1   0.0014000   22      -13       9900014      311      111") 
  P8gen.SetParameters("411:addChannel = 1   0.0027000   22      -13       9900014     -321      211") 
  # overwrite D0 decays
  P8gen.SetParameters("421:new  D0  Dbar0    1   0   0    1.86486    0.00000    0.00000    0.00000  1.22900e-01   0   1   0   1   0")
  P8gen.SetParameters("421:addChannel = 1   0.0034000   22      -11       9900014     -211") 
  P8gen.SetParameters("421:addChannel = 1   0.0022000   22      -11       9900014     -213") 
  P8gen.SetParameters("421:addChannel = 1   0.0350000   22      -11       9900014     -321") 
  P8gen.SetParameters("421:addChannel = 1   0.0225000   22      -11       9900014     -323")
  P8gen.SetParameters("421:addChannel = 1   0.0015000   22      -11       9900014     -325") 
  P8gen.SetParameters("421:addChannel = 1   0.0014000   22      -11       9900014   -10323") 
  P8gen.SetParameters("421:addChannel = 1   0.0034000   22      -13       9900014     -211") 
  P8gen.SetParameters("421:addChannel = 1   0.0022000   22      -13       9900014     -213") 
  P8gen.SetParameters("421:addChannel = 1   0.0340000   22      -13       9900014     -321")
  P8gen.SetParameters("421:addChannel = 1   0.0214000   22      -13       9900014     -323") 
  P8gen.SetParameters("421:addChannel = 1   0.0015000   22      -13       9900014     -325") 
  P8gen.SetParameters("421:addChannel = 1   0.0014000   22      -13       9900014   -10323") 
  P8gen.SetParameters("421:addChannel = 1   0.0011000   22      -11       9900014      311     -211") 
  P8gen.SetParameters("421:addChannel = 1   0.0006000   22      -11       9900014     -321      111") 
  P8gen.SetParameters("421:addChannel = 1   0.0011000   22      -13       9900014      311     -211") 
  P8gen.SetParameters("421:addChannel = 1   0.0006000   22      -13       9900014     -321      111") 
  # overwrite tau decays
  P8gen.SetParameters("15:new  tau-  tau+   2  -3   0    1.77682    0.00000    0.00000    0.00000  8.71100e-02   0   1   0   1   0")
  P8gen.SetParameters("15:addChannel  1   0.1076825 1521       9900014     -211") 
  P8gen.SetParameters("15:addChannel  1   0.0069601 1521       9900014     -321") 
  P8gen.SetParameters("15:addChannel  1   0.1772832 1531       9900014       11      -12") 
  P8gen.SetParameters("15:addChannel  1   0.1731072 1531       9900014       13      -14") 
  P8gen.SetParameters("15:addChannel  1   0.2537447 1532       9900014      111     -211")
  P8gen.SetParameters("15:addChannel  1   0.0015809 1532       9900014      311     -321") 
  P8gen.SetParameters("15:addChannel  1   0.0001511 1532       9900014      221     -321") 
  P8gen.SetParameters("15:addChannel  1   0.0083521 1533       9900014     -211     -311")
  P8gen.SetParameters("15:addChannel  1   0.0042655 1533       9900014      111     -321") 
  P8gen.SetParameters("15:addChannel  1   0.0924697 1541       9900014      111      111     -211") 
  P8gen.SetParameters("15:addChannel  1   0.0925691 1541       9900014     -211     -211      211") 
  P8gen.SetParameters("15:addChannel  1   0.0039772 1542       9900014      111     -211     -311") 
  P8gen.SetParameters("15:addChannel  1   0.0034701 1542       9900014     -211      211     -321") 
  P8gen.SetParameters("15:addChannel  1   0.0014318 1542       9900014     -211     -321      321") 
  P8gen.SetParameters("15:addChannel  1   0.0015809 1542       9900014      111      311     -321") 
  P8gen.SetParameters("15:addChannel  1   0.0011932 1542       9900014      130     -211      310") 
  P8gen.SetParameters("15:addChannel  1   0.0006463 1542       9900014      111      111     -321") 
  P8gen.SetParameters("15:addChannel  1   0.0002386 1542       9900014      130      130     -211") 
  P8gen.SetParameters("15:addChannel  1   0.0002386 1542       9900014     -211      310      310") 
  P8gen.SetParameters("15:addChannel  1   0.0013821 1543       9900014      111     -211      221 ")
  P8gen.SetParameters("15:addChannel  1   0.0017520 1544       9900014       22      111     -211") 
  P8gen.SetParameters("15:addChannel  1   0.0459365 1551       9900014      111     -211     -211      211 ")
  P8gen.SetParameters("15:addChannel  1   0.0104401 1551       9900014      111      111      111     -211") 
  P8gen.SetParameters("15:addChannel  1   0.0049069 1561       9900014      111      111     -211     -211      211") 
  P8gen.SetParameters("15:addChannel  1   0.0009515 1561       9900014      111      111      111      111     -211") 
  P8gen.SetParameters("15:addChannel  1   0.0008342 1561       9900014     -211     -211     -211      211      211 ")
  P8gen.SetParameters("15:addChannel  1   0.0001631    0       9900014     -211     -211      211      221") 
  P8gen.SetParameters("15:addChannel  1   0.0001491    0       9900014      111      111     -211      221 ")
  P8gen.SetParameters("15:addChannel  1   0.0001392    0       9900014      111      111     -211      223 ")
  P8gen.SetParameters("15:addChannel  1   0.0001193    0       9900014     -211     -211      211      223 ")
  P8gen.SetParameters("15:addChannel  1   0.0004077    0       9900014      223     -321 ")
  P8gen.SetParameters("15:addChannel  1   0.0004773    0       9900014      111      111      111     -321") 
  P8gen.SetParameters("15:addChannel  1   0.0003052    0       9900014      111     -211      211     -321 ")
  P8gen.SetParameters("15:addChannel  1   0.0002784    0       9900014      221     -323 ")
  P8gen.SetParameters("15:addChannel  1   0.0002366    0       9900014      111      111     -211     -311 ")
  P8gen.SetParameters("15:addChannel  1   0.0002237    0       9900014     -211     -211      211     -311 ")
  P8gen.SetParameters("15:addChannel  1   0.0002953    0       9900014      111     -211     -311      311 ")
  P8gen.SetParameters("15:addChannel  1   0.0000590    0       9900014      111     -211     -321      321 ")

