# setenv LD_LIBRARY_PATH ${LD_LIBRARY_PATH}:/media/ShipSoft/genfit-build/lib
inputFile = 'ship.Pythia8-TGeant4.root'
debug = False
withNoAmbiguities = None # True   for debugging purposes
nEvents   = 99999
withHists = True
vertexing = True
dy = None

import ROOT,os,sys,getopt
from pythia8_conf import addHNLtoROOT
import rootUtils as ut
try:
        opts, args = getopt.getopt(sys.argv[1:], "o:D:FHPu:n:f:c:hqv:sl:A:Y:i",["inputFile=","nEvents=","ambiguities","noVertexing"])
except getopt.GetoptError:
        # print help information and exit:
        print ' enter --inputFile=  --nEvents= number of events to process, ambiguities wire ambiguities default none' 
        print ' outputfile will have same name with _rec added'   
        sys.exit()
for o, a in opts:
        if o in ("noVertexing"):
            vertexing = False
        if o in ("ambiguities"):
            withNoAmbiguities = True
        if o in ("-f", "--inputFile"):
            inputFile = a
        if o in ("-n", "--nEvents="):
            nEvents = int(a)
        if o in ("-Y"): 
            dy = float(a)
            inputFile = 'ship.'+str(dy)+'.Pythia8-TGeant4.root'

# need to figure out which geometry was used
if not dy:
  # try to extract from input file name
  tmp = inputFile.split('.')
  try:
    dy = float( tmp[1]+'.'+tmp[2] )
  except:
    dy = None
print 'configured to process ',nEvents,' events from ' ,inputFile, ' with option Yheight = ',dy,' with vertexing',vertexing
outFile = inputFile.replace('.root','_rec.root') 
os.system('cp '+inputFile+' '+outFile)

if withHists:
 h={}
 ut.bookHist(h,'distu','distance to wire',100,0.,5.)
 ut.bookHist(h,'distv','distance to wire',100,0.,5.)
 ut.bookHist(h,'disty','distance to wire',100,0.,5.)
 ut.bookHist(h,'nmeas','nr measuerements',100,0.,50.)
#-----prepare python exit-----------------------------------------------
def pyExit():
 global fitter
 del fitter
 print "finishing pyExit" 
import atexit
atexit.register(pyExit)

from array import array
import shipunit as u
import rootUtils as ut
from ShipGeoConfig import ConfigRegistry
if dy: 
 ShipGeo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/geometry_config.py", Yheight = dy )
else:
 ShipGeo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/geometry_config.py")
# -----Create geometry----------------------------------------------
import shipDet_conf
run = ROOT.FairRunSim()
modules = shipDet_conf.configure(run,ShipGeo)

addHNLtoROOT()

fout = ROOT.TFile(outFile,'update')

def myVertex(t1,t2,PosDir):
 # closest distance between two tracks
   V=0
   for i in range(3):   V += PosDir[t1]['direction'](i)*PosDir[t2]['direction'](i)
   S1=0
   for i in range(3):   S1 += (PosDir[t1]['position'](i)-PosDir[t2]['position'](i))*PosDir[t1]['direction'](i)
   S2=0
   for i in range(3):   S2 += (PosDir[t1]['position'](i)-PosDir[t2]['position'](i))*PosDir[t2]['direction'](i)
   l = (S2-S1*V)/(1-V*V)
   x2 = PosDir[t2]['position'](0)+l*PosDir[t2]['direction'](0)
   y2 = PosDir[t2]['position'](1)+l*PosDir[t2]['direction'](1)
   z2 = PosDir[t2]['position'](2)+l*PosDir[t2]['direction'](2)
   x1 = PosDir[t1]['position'](0)+l*PosDir[t1]['direction'](0)
   y1 = PosDir[t1]['position'](1)+l*PosDir[t1]['direction'](1)
   z1 = PosDir[t1]['position'](2)+l*PosDir[t1]['direction'](2)
   dist = ROOT.TMath.Sqrt((x1-x2)**2+(y1-y2)**2+(z1-z2)**2)
   return (x1+x2)/2.,(y1+y2)/2.,(z1+z2)/2.,dist

class ShipReco:
 " convert FairSHiP MC hits to measurements"
 def __init__(self,fn):
  self.sTree     = fn.cbmsim
  if self.sTree.GetBranch("GeoTracks"): self.sTree.SetBranchStatus("GeoTracks",0)
  self.nEvents   = min(self.sTree.GetEntries(),nEvents)
# prepare for output
  self.fPartArray   = ROOT.TClonesArray("TParticle") 
  self.fGenFitArray = ROOT.TClonesArray("genfit::Track") 
  self.fGenFitArray.BypassStreamer(ROOT.kFALSE)
  self.fitTrack2MC  = ROOT.std.vector('int')()
  self.SmearedHits  = ROOT.TClonesArray("TVectorD") 

  if self.sTree.GetBranch("FitTracks"):
   self.sTree.SetBranchAddress("FitTracks", self.fGenFitArray)
   self.sTree.SetBranchAddress("Particles",self.fPartArray)
   self.sTree.SetBranchAddress("SmearedHits",self.SmearedHits)
   self.Particles   = self.sTree.GetBranch("Particles")  
   self.fitTracks   = self.sTree.GetBranch("FitTracks")  
   self.SHbranch    = self.sTree.GetBranch("SmearedHits")
   self.mcLink      = self.sTree.GetBranch("fitTrack2MC")
   print "branch already exists !"
  else :
   self.Particles   = self.sTree.Branch("Particles",self.fPartArray,32000,-1)
   self.SHbranch    = self.sTree.Branch( "SmearedHits",self.SmearedHits,32000,-1)
   self.fitTracks   = self.sTree.Branch( "FitTracks",self.fGenFitArray,32000,-1)  
   self.mcLink      = self.sTree.Branch( "fitTrack2MC",self.fitTrack2MC,32000,-1)  
  self.random = ROOT.TRandom()
  ROOT.gRandom.SetSeed(13)
#
 def hit2wire(self,ahit,no_amb=None):
     detID = ahit.GetDetectorID()
     top = ROOT.TVector3()
     bot = ROOT.TVector3()
     modules["Strawtubes"].StrawEndPoints(detID,bot,top)
     ex = ahit.GetX()
     ey = ahit.GetY()
     ez = ahit.GetZ()
   #distance to wire, and smear it.
     dw  = ahit.dist2Wire()
     smear = 0
     if not no_amb: smear = ROOT.fabs(self.random.Gaus(dw,ShipGeo.straw.resol))
     smearedHit = {'mcHit':ahit,'xtop':top.x(),'ytop':top.y(),'z':top.z(),'xbot':bot.x(),'ybot':bot.y(),'z':bot.z(),'dist':smear}
     # print 'smeared hit:',top.x(),top.y(),top.z(),bot.x(),bot.y(),bot.z(),"dist",smear,ex,ey,ez,ox,oy,oz
     if abs(top.y())==abs(bot.y()): h['disty'].Fill(dw)
     if abs(top.y())>abs(bot.y()): h['distu'].Fill(dw)
     if abs(top.y())<abs(bot.y()): h['distv'].Fill(dw)
     return smearedHit
  
 def execute(self,n):
  if n > self.nEvents-1: return None 
  rc    = self.sTree.GetEvent(n) 
  if n%1000==0: print "==> event ",n
  nShits = self.sTree.strawtubesPoint.GetEntriesFast() 
  hitPosLists = {}
  self.SmearedHits.Clear()
  self.fPartArray.Clear()
  self.fGenFitArray.Clear()
  self.fitTrack2MC.clear()
  for i in range(nShits):
    ahit = self.sTree.strawtubesPoint.At(i)
    sm   = self.hit2wire(ahit,withNoAmbiguities)
    m = array('d',[i,sm['xtop'],sm['ytop'],sm['z'],sm['xbot'],sm['ybot'],sm['z'],sm['dist']])
    measurement = ROOT.TVectorD(8,m)
# copy to branch
    nHits = self.SmearedHits.GetEntries()
    if self.SmearedHits.GetSize() == nHits: self.SmearedHits.Expand(nHits+1000)
    self.SmearedHits[nHits]=measurement 
    if ahit.GetDetectorID() > 5*10000000 : continue
    # do not use hits in Veto station for track reco   
    trID = ahit.GetTrackID()
    if not hitPosLists.has_key(trID):   
      hitPosLists[trID] = ROOT.std.vector('TVectorD')()
    m = array('d',[sm['xtop'],sm['ytop'],sm['z'],sm['xbot'],sm['ybot'],sm['z'],sm['dist']])
    measurement = ROOT.TVectorD(7,m)
    hitPosLists[trID].push_back(measurement) 
  fitTrack = {}
  nTrack = -1
  for atrack in hitPosLists:
   if atrack < 0: continue # these are hits not assigned to MC track because low E cut
   pdg    = self.sTree.MCTrack[atrack].GetPdgCode()
   if not PDG.GetParticle(pdg): continue # unknown particle
   meas = hitPosLists[atrack]
   nM = meas.size()
   if nM < 25 : continue # not enough hits to make a good trackfit 
   if debug: 
       mctrack = self.sTree.MCTrack[atrack]
   charge = PDG.GetParticle(pdg).Charge()/(3.)
   posM = ROOT.TVector3(0, 0, 0)
   momM = ROOT.TVector3(0,0,3.*u.GeV)
# approximate covariance
   covM = ROOT.TMatrixDSym(6)
   resolution = 0.02 #0.01
   for  i in range(3):   covM[i][i] = resolution*resolution
   for  i in range(3,6): covM[i][i] = ROOT.TMath.pow(resolution / nM / ROOT.TMath.sqrt(3), 2)
# trackrep
   rep = ROOT.genfit.RKTrackRep(pdg)
# smeared start state
   stateSmeared = ROOT.genfit.MeasuredStateOnPlane(rep)
   rep.setPosMomCov(stateSmeared, posM, momM, covM)
# create track
   seedState = ROOT.TVectorD(6)
   seedCov   = ROOT.TMatrixDSym(6)
   rep.get6DStateCov(stateSmeared, seedState, seedCov)
   fitTrack[atrack] = ROOT.genfit.Track(rep, seedState, seedCov)
   ROOT.SetOwnership(fitTrack[atrack], False)
   for m in meas:
      hitCov = ROOT.TMatrixDSym(7)
      hitCov[6][6] = resolution*resolution
      tp = ROOT.genfit.TrackPoint(fitTrack[atrack]) # note how the point is told which track it belongs to 
      measurement = ROOT.genfit.WireMeasurement(m,hitCov,1,6,tp) # the measurement is told which trackpoint it belongs to
      tp.addRawMeasurement(measurement) # package measurement in the TrackPoint                                          
      fitTrack[atrack].insertPoint(tp)  # add point to Track
#check
   if not fitTrack[atrack].checkConsistency():
    print 'Problem with track before fit, not consistent',self.fitTrack[atrack]
    continue
# do the fit
   try:    fitter.processTrack(fitTrack[atrack])
   except: 
       print "genfit failed to fit track"
       continue
#check
   if not fitTrack[atrack].checkConsistency():
    print 'Problem with track after fit, not consistent',self.fitTrack[atrack]
    continue
   fitStatus   = fitTrack[atrack].getFitStatus()
   chi2        = fitStatus.getChi2()
# make track persistent
   nTrack   = SHiP.fGenFitArray.GetEntries()
   theTrack = ROOT.genfit.Track(fitTrack[atrack])
   self.fGenFitArray[nTrack] = theTrack
   self.fitTrack2MC.push_back(atrack)
   if debug: 
    print 'save track',theTrack,chi2,nM,fitStatus.isFitConverged()
    if nM > 28:  
     display.addEvent(fitTrack[atrack])
  return nTrack+1
#
 def find2TrackVertex(self):
  fittedTracks = self.fGenFitArray
  LV     = {}
  PosDirCharge = {} 
  for tr in range(fittedTracks.GetEntries()):
   fitStatus = fittedTracks[tr].getFitStatus()
   if not fitStatus.isFitConverged(): continue
   nmeas = fittedTracks[tr].getNumPoints()
   chi2  = fitStatus.getChi2()/nmeas
   if chi2<50 and not chi2<0: 
      xx  = fittedTracks[tr].getFittedState()
      PosDirCharge[tr] = {'position':xx.getPos(),'direction':xx.getDir(),'momentum':xx.getMom(),'charge':xx.getCharge(),'pdgCode':xx.getPDG()}
#
  if len(PosDirCharge) < 2: return
  (PosDirCharge.keys()).sort()
  for t1 in PosDirCharge:
   c1  = PosDirCharge[t1]['charge'] 
   LV1 = ROOT.TLorentzVector()
   for t2 in PosDirCharge:
     if not t2>t1: continue
     if PosDirCharge[t2]['charge'] == c1 : continue
     LV2 = ROOT.TLorentzVector()
     xv,yv,zv,doca = myVertex(t1,t2,PosDirCharge)
     HNLPos = ROOT.TVector3(xv,yv,zv)
     # make a new rep for track 1
     rep = ROOT.genfit.RKTrackRep(PosDirCharge[t1]['pdgCode'])
     state = ROOT.genfit.StateOnPlane(rep)
     rep.setPosMom(state, PosDirCharge[t1]['position'],PosDirCharge[t1]['momentum'])
     origPlane = state.getPlane()
     origState = ROOT.genfit.StateOnPlane(state)
     try:
       rep.extrapolateToPoint(state, HNLPos, False)
     except:
       print 'extrap did not worked'
       continue 
     mass = PDG.GetParticle(PosDirCharge[t1]['pdgCode']).Mass()
     mom  = rep.getMom(state)  
     E = ROOT.TMath.Sqrt( mass*mass + mom.Mag2() )
     LV1.SetPxPyPzE(mom.x(),mom.y(),mom.z(),E)
     # make a new rep for track 2
     rep = ROOT.genfit.RKTrackRep(PosDirCharge[t2]['pdgCode'])
     state = ROOT.genfit.StateOnPlane(rep)
     rep.setPosMom(state, PosDirCharge[t2]['position'],PosDirCharge[t2]['momentum'])
     origPlane = state.getPlane()
     origState = ROOT.genfit.StateOnPlane(state)
     try:
       rep.extrapolateToPoint(state, HNLPos, False)
     except:
       print 'extrap did not worked'
       continue 
     mass = PDG.GetParticle(PosDirCharge[t2]['pdgCode']).Mass()
     mom  = rep.getMom(state)  
     E = ROOT.TMath.Sqrt( mass*mass + mom.Mag2() )
     LV2.SetPxPyPzE(mom.x(),mom.y(),mom.z(),E)
     HNL = LV1+LV2
# try to make it persistent
     vx = ROOT.TLorentzVector(HNLPos,0.)  # time not set
     particle = ROOT.TParticle(9900014,0,-1,-1,t1,t2,HNL,vx)
     nParts   = self.fPartArray.GetEntries()
     self.fPartArray[nParts] = particle 
     #
     HNLMom = ROOT.TLorentzVector()
     particle.Momentum(HNLMom)

geoMat =  ROOT.genfit.TGeoMaterialInterface()
PDG = ROOT.TDatabasePDG.Instance()
# init geometry and mag. field
tgeom = ROOT.TGeoManager("Geometry", "Geane geometry")
geofile = inputFile.replace('ship.','geofile_full.')
tgeom.Import(geofile)
#
bfield = ROOT.genfit.BellField(ShipGeo.Bfield.max ,ShipGeo.Bfield.z,2)
fM = ROOT.genfit.FieldManager.getInstance()
fM.init(bfield)
 
geoMat =  ROOT.genfit.TGeoMaterialInterface()
ROOT.genfit.MaterialEffects.getInstance().init(geoMat)
if debug: # init event display
 display = ROOT.genfit.EventDisplay.getInstance()

# init fitter
fitter          = ROOT.genfit.KalmanFitterRefTrack()
if debug: fitter.setDebugLvl(1) # produces lot of printout
WireMeasurement = ROOT.genfit.WireMeasurement
# access ShipTree
SHiP = ShipReco(fout)

# main loop
for iEvent in range(0, SHiP.nEvents):
 ntracks = SHiP.execute(iEvent)
 if vertexing:
# now go for 2-track combinations
   if ntracks > 1: SHiP.find2TrackVertex()
# make tracks and particles persistent
 if debug: print 'call Fill', len(SHiP.fGenFitArray),ntracks,SHiP.fGenFitArray.GetEntries()
 SHiP.Particles.Fill()
 SHiP.fitTracks.Fill()
 SHiP.mcLink.Fill()
 SHiP.SHbranch.Fill()

 if debug: print 'end of event after Fill'
 
# end loop over events

print 'finished writing tree'
SHiP.sTree.Write()

if debug:
# open event display
 display.open() 



