# -*- coding: utf-8 -*-
'''
This Code organizes the FMU Interfaces  "FMUInterface.py" and "FMIDescription.py" 
in a python class. Its the main class that shoudl be used by 3rd party applications.

'''
#
#

# filename: contsim.py
# author: - Thomas Meschede
#
# 
# Test simulation of FMI files using the provided FMI Interface from pysimulator from DLR
#
#
#
# modified:
#       - 2012 11 22 - Thomas Meschede

#python2 tweaks:
from __future__ import print_function

import numpy as np
import ctypes
import types
import sys
#print(sys.path)
from . import FMUInterface2 as fmu2
from .FMUInterface2 import fmiTrue, fmiFalse, fmiValueReference,fmiValueReferenceVector
import re

"""fmiFalse = 0
fmiTrue = 1
fmiReal = ctypes.c_double
fmiInteger = ctypes.c_int
fmiBoolean = ctypes.c_int
fmiString = ctypes.c_char_p
fmiRealVector = ctypes.POINTER(fmiReal)
fmiIntegerVector = ctypes.POINTER(fmiInteger)
fmiBooleanVector = ctypes.POINTER(fmiBoolean)
fmiStringVector = ctypes.POINTER(fmiString)
fmiBooleanPtr = ctypes.POINTER(fmiBoolean)
fmiComponent = ctypes.c_void_p
fmiComponentEnvironment = ctypes.c_void_p
fmiStatus = ctypes.c_int
fmiValueReference = ctypes.c_uint
fmiValueReferenceVector = ctypes.POINTER(fmiValueReference)
fmiType = ctypes.c_uint
fmiFMUstate = ctypes.c_void_p
fmiFMUstatePtr = ctypes.POINTER(fmiFMUstate)
fmiByte = ctypes.c_char
fmiByteVector = ctypes.POINTER(fmiByte)
fmiStatusKind = ctypes.c_uint"""

#/** FMI 1.0 status codes */
fmiStatus=dict(fmiOK = 0,
    fmiWarning = 1,
    fmiDiscard = 2,
    fmiError = 3,
    fmiFatal = 4,
    fmiPending = 5)

class Struct:
    def __init__(self, **entries): 
        self.__dict__.update(entries)
        self.__revdict__= {v: k for k, v in self.__dict__.items()}
    
    def rev(self,arg):
        return self.__revdict__[arg]

fmiStatus = Struct(**fmiStatus)

class fmi(fmu2.FMUInterface):
  def __init__(self, file, loggingOn = True):
    super(fmi, self).__init__(file, loggingOn = loggingOn, preferredFmiType="cs") #init fmu interface
    
    self.changedStartValue={}
    self.loggingOn=loggingOn
    print("FMI Version: {}".format(self._fmiGetVersion()))
    print("typesplatform: {}".format(self._fmiGetTypesPlatform()))

#  def getStateNames(self):
#      ''' Returns a list of Strings: the names of all states in the model.
#      '''
#      references = self.fmiGetStateValueReferences()
#      allVars = list(self.description.scalarVariables.items())
#      referenceListSorted = [(index, var[1].valueReference) for index, var in enumerate(allVars)]
#      referenceListSorted.sort(key=itemgetter(1))
#      referenceList = [r[1] for r in referenceListSorted]
#
#      names = []
#      for ref in references:
#          if ref == -1:
#              # No reference available -> name is hidden
#              names.append('')
#          else:
#              k = referenceList.count(ref)
#              if k > 0:
#                  index = -1
#                  i = 0
#                  while i < k:
#                      i += 1
#                      index = referenceList.index(ref, index + 1)
#                      if allVars[referenceListSorted[index][0]][1].alias is None:
#                          name = allVars[referenceListSorted[index][0]][0]
#                          names.append(name)
#                          break
#              else:
#                  # Reference not found. Should not occur.
#                  names.append('')
#      return names

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    print("freefmu...")
    fmu.free()    

  def getInputVariables(self):
    vars = [(name, var.type.start) for (name, var) in self.description.scalarVariables.items() if var.causality == 'input']
    return vars

  def searchvars(self,string):
    r = re.compile(string)  #search for variables to plot
    vmatch = np.vectorize(lambda x:bool(r.match(x)))

    #A = np.array(list('abc abc abc'))
    #sel = vmatch(A)

    vrs = np.array(self.getVariables())[:,0]
    #myfmu.getVariables()
    return vrs[vmatch(vrs)]

  def getVariables(self):
    vars = [(name, var.type.start) for (name, var) in self.description.scalarVariables.items()]
    return vars

  def getStartValues(self,varlist):
    allvars = self.description.scalarVariables
    vars = [(name,allvars[name].type.start) for name in varlist]
    return vars

  def getValue(self, name):
      ''' Returns the values of the variables given in name;
          name is either a String or a list of Strings.
      '''
      if type(name) == list:
          n = len(name)
          nameList = True
          names = name
      else:
          n = 1
          nameList = False
          names = [name]

      iReal = []
      iInteger = []
      iBoolean = []
      iString = []
      refReal = []
      refInteger = []
      refBoolean = []
      refString = []
      for i, x in enumerate(names):
          dataType = self.description.scalarVariables[x].type.basicType
          if dataType == 'Real':
              refReal.append(self.description.scalarVariables[x].valueReference)
              iReal.append(i)
          elif dataType == 'Integer':
              refInteger.append(self.description.scalarVariables[x].valueReference)
              iInteger.append(i)
          elif dataType == 'Boolean':
              refBoolean.append(self.description.scalarVariables[x].valueReference)
              iBoolean.append(i)
          elif dataType == 'String':
              refString.append(self.description.scalarVariables[x].valueReference)
              iString.append(i)

      retValue = list(range(n))
      k = len(refReal)
      if k > 0:
          ref = fmu2.createfmiReferenceVector(k)
          for i in range(k):
              ref[i] = refReal[i]
          status, values = self.fmiGetReal(ref)
          for i in range(k):
              retValue[iReal[i]] = values[i]
      k = len(refInteger)
      if k > 0:
          ref = fmu2.createfmiReferenceVector(k)
          for i in range(k):
              ref[i] = refInteger[i]
          status, values = self.fmiGetInteger(ref)
          for i in range(k):
              retValue[iInteger[i]] = values[i]
      k = len(refBoolean)
      if k > 0:
          ref = fmu2.createfmiReferenceVector(k)
          for i in range(k):
              ref[i] = refBoolean[i]
          status, values = self.fmiGetBoolean(ref)
          for i in range(k):
              retValue[iBoolean[i]] = values[i]
      k = len(refString)
      if k > 0:
          ref = fmu2.createfmiReferenceVector(k)
          for i in range(k):
              ref[i] = refString[i]
          status, values = self.fmiGetString(ref)
          for i in range(k):
              retValue[iString[i]] = values[i]

      if nameList:
          return retValue
      else:
          return retValue[0]
    
  def setValues(self, valuelist):
      for name, val in valuelist:
          self.setValue(name,val)
    
  def setValue(self, valueName, valueValue):
        ''' set the variable valueName to valueValue
            @param valueName: name of variable to be set
            @type valueName: string
            @param valueValue: new value
            @type valueValue: any type castable to the type of the variable valueName
        '''
        ScalarVariableReferenceVector = fmu2.createfmiReferenceVector(1)
        ScalarVariableReferenceVector[0] = self.description.scalarVariables[valueName].valueReference
        if self.description.scalarVariables[valueName].type.basicType == 'Real':
            ScalarVariableValueVector = fmu2.createfmiRealVector(1)
            ScalarVariableValueVector[0] = float(valueValue)
            self.fmiSetReal(ScalarVariableReferenceVector, ScalarVariableValueVector)
        elif self.description.scalarVariables[valueName].type.basicType in ['Integer', 'Enumeration']:
            ScalarVariableValueVector = fmu2.createfmiIntegerVector(1)
            ScalarVariableValueVector[0] = int(valueValue)
            self.fmiSetInteger(ScalarVariableReferenceVector, ScalarVariableValueVector)
        elif self.description.scalarVariables[valueName].type.basicType == 'Boolean':
            ScalarVariableValueVector = fmu2.createfmiBooleanVector(1)
            ScalarVariableValueVector[0] = fmiTrue if valueValue == "true" else fmiFalse
            self.fmiSetBoolean(ScalarVariableReferenceVector, ScalarVariableValueVector)
        elif self.description.scalarVariables[valueName].type.basicType == 'String':
            ScalarVariableValueVector = fmu2.createfmiStringVector(1)
            ScalarVariableValueVector[0] = valueValue.encode()
            self.fmiSetString(ScalarVariableReferenceVector, valueValue)
            #self.fmiSetString(ScalarVariableReferenceVector, ctypes.c_char_p(valueValue))

  def printvarprops(self):
      ''' Returns a list of Strings: the names of all output variables in the model.
      '''
      names = {}
      for key,var in self.description.scalarVariables.items():
          #if var.causality=='output':
            print("{:<40}{v.valueReference:<30}{v.alias:<20}{v.variability}".format(key,v=var))#key, var.valueReference, var.alias, var.variability, var.description, var.causality,var.directDependency,  var.type)
            #names[var.valueReference]=key
              
      return names      

  def getOutputNames(self):
      ''' Returns a list of Strings: the names of all output variables in the model.
      '''
      names = {}
      for key,var in self.description.scalarVariables.items():
          if var.causality=='output':
            #print(key, var.valueReference, var.alias, var.variability, var.description, var.causality,var.directDependency,  var.type)
            names[var.valueReference]=key
              
      return names      

  def getDerivatives(self, t, x):
      ''' Returns the right hand side of the dynamic system for
          given time t and state vector x.
          #x is 1d numpy array
      '''
      self.interface.fmiSetTime(t)
      if self.description.numberOfContinuousStates == 0:
          dx = np.zeros([1, ])
      else:
          self.interface.fmiSetContinuousStates(x)
          status, dx = self.interface.fmiGetDerivatives()

  def getStateNames(self):
      ''' Returns a list of Strings: the names of all states in the model.
      '''
      '''references = self.fmiGetStateValueReferences()

      names = {}
      for key,var in self.description.scalarVariables.items():
          if var.valueReference in references and var.variability=='continuous':
            #print(key, var.valueReference, var.alias, var.variability, var.description, var.causality,var.directDependency,  var.type)
            names[var.valueReference]=key
              
      return names'''
      print("FMU2.0 not working yet ...")

  def _setDefaultStartValues(self):
      ''' Reads given start values from FMI model description and sets variables accordingly
      '''
      for index in self.description.scalarVariables:
          if self.description.scalarVariables[index].type.start != None:
              #print(index, self.description.scalarVariables[index].type.start)
              self.setValue(index, self.description.scalarVariables[index].type.start)

  def initialize(self, tStart, tStop, errorTolerance=1e-9):
      ''' Initializes the model at time = t with
          changed start values given by the dictionary
          self.changedStartValue.
          The function returns a status flag and the next time event.
      '''
      self.fmiInstantiate()

      if self.activeFmiType == 'me':    
          # Set start time
          self.fmiSetTime(tStart)
          
      # Set start values
      self._setDefaultStartValues()
      for name in self.changedStartValue.keys():
          self.setValue(name, self.changedStartValue[name])
      # Initialize model
#        (eventInfo, status) = self.interface.fmiInitialize(fmiTrue, errorTolerance)
      s1 = self.fmiSetupExperiment(fmiTrue, errorTolerance, tStart, fmiTrue, tStop)
      s2 = self.fmiEnterInitializationMode()
      s3 = self.fmiExitInitializationMode()
      
      status = max(s1,s2,s3)
      nextTimeEvent = None

      # status > 1 means error during initialization        
      return status, nextTimeEvent
        
      
#      # Terminate last simulation in model
#      #self.interface.fmiTerminate()
#      #print("Set start time")
#      #self.interface.fmiSetTime(t)
#      # Set start values
#      #self._setDefaultStartValues()
#      for name in list(self.changedStartValue.keys()):
#          self.setValue(name, self.changedStartValue[name])
#      # Initialize model
#      eventInfo, status = self.fmiInitialize(fmiTrue, errorTolerance)
#      x0 = self.fmiGetContinuousStates()
#      return x0, status, eventInfo
      

  def f(self,t,y):
      """ return a function which can be used for external solver
      
      the example (just small differences, no jacobian) from the scipy intergrator:
      
      http://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.ode.html#scipy.integrate.ode
      
      The integration:
         f = myfmu.f #loaded FMU
         t0 = 0.0
         y0 = myfmu.initialize(0.0)

         r = ode(f).set_integrator('zvode', method='bdf')
         r.set_initial_value(y0, t0)
         t1 = 10
         dt = 1
         while r.successful() and r.t < t1:
             r.integrate(r.t+dt)
             print("%g %g" % (r.t, r.y))
      """
      
      self.fmiSetTime(t)
      self.fmiSetContinuousStates(y)
      
      ny = self.fmiGetDerivatives()
      
      return ny

  def single_timestep(self, dt = 0.01):
    pass

  def simulate(self,dt=0.01, t_start=0.0, t_end=1.0, varnames=[], inputfs = [], initialize=False, datares = 100):
    """simulates an fmu with inputfunctions and datares ()"""
    if self.activeFmiType == 'me':
      if self.loggingOn: print("run me-simulation")
      return self.mesimulate(dt, t_start, t_end, varnames, inputfs =  inputfs)
    elif self.activeFmiType == 'cs':
      if self.loggingOn: print("run co-simulation")
      return self.cosimulate(dt, t_start, t_end, varnames, inputfs = inputfs, initialize = initialize, datares = datares)

  def mesimulate(self,dt=0.01, t_start=0.0, t_end=1.0, varnames=[], inputfs = []):
    def RK4(y,t,h,f):
        h05 = h * .5
        t05 = t + h05
        k1=f(t,y);
        k2=f(t05,y+h05*k1);
        k3=f(t05,y+h05*k2);
        k4=f(t+h,y+h*k3);
        yn=y+h/6.0*(k1+2*(k2+k3)+k4)
        return yn

    self.fmiSetTime(0.0)

    x,status,eventInfo = self.initialize(0.0)

    res = [[0.0]+[self.getValue(varname) for varname in varnames]]
    #integration loop
    for t in np.arange(t_start,t_end + dt,dt):
      #x = x + dt * self.f(t,x) #explicit euler
      x = RK4(x,t,dt,self.f) #explicit Runge-Kutta 4 (RK4)
     
      self.fmiCompletedIntegratorStep()
      
      #save results in array
      #print(t,x,dx)
      step=[[t+dt]+[self.getValue(varname) for varname in varnames]]
      if np.nan in step:
        print(step)
        break
      #time.sleep(dt)
      res+=step
      
    
    self.fmiTerminate()
    
    return np.array(res)

  def cosimulate(self, dt=0.01, t_start = 0.0, t_end = 1.0, varnames=[], inputfs = [],
                 startvalues = [], initialize = False, datares = 100, dt_min = 1e-40):#TODO: datares integrieren
    if initialize:
        status,nextTimeEvent = self.initialize(0.0,t_end)
        
        assert not isinstance(varnames, str)
        
        if status > 1:
            print("Model initialization failed. fmiStatus = " + str(status))
        
        #self.setValue("x",3.1) ##setting input functions
    
    for name,val in startvalues:
        self.setValue(name,val)
    
    dtype = [("t","float")]+[(name,"float") for name in varnames]
    res=[]
    t = t_start #current master time
    t_succ = t
    inloop = True
    lastperc = 0
    dt_tmp = dt
    print("running:")
    while inloop:
      #TODO: enable input functions
      for names,func in inputfs:
        for name,val in zip(names,func(t)):
            #print(t,name,val)
            self.setValue(name, val)
        #inloop = False
      status = self.fmiDoStep(t, dt_tmp, fmiTrue) 
      #print(self.getValue(['x','der(x)']))
      step=tuple([t]+[self.getValue(varname) for varname in varnames])
      #if t>3.0 and t<3.1: self.setValue("x",3.1)          
      if status > 2:
          if t >= t_end: print("simulation finished succesful")
          elif dt_tmp>dt_min:
              dt_tmp = dt_tmp/2.0
              if self.loggingOn: print("smaller stepsize: {}".format(dt_tmp))
              continue
          #elif t > t_succ:
          #    t = t_succ
          #    dt_tmp = 
          else:
              if dt_tmp < dt_min: print("smallest step size reached ({})!".format(dt_tmp))
              print("an error: <{}> in doStep at time = {:.2e}".format(fmiStatus.rev(status),t))
          # Raise exception to abort simulation...
          self.finalize()
          break
      elif status == 2:  # Discard
          status, info = self.fmiGetBooleanStatus(3) # fmi2Terminated
          if info == fmiTrue:
              status, lastTime = self.fmiGetRealStatus(2)       # fmi2LastSuccessfulTime
              t = lastTime
              inloop = False
          else:
              print("Not supported status in doStep at time = {:.2e}".format(t))
              # Raise exception to abort simulation...
              break
      elif status < 2:
          t_succ = t
          t += dt
          dt_tmp = dt
          res.append(step)   
          perc = round(t/t_end*100.0)
          if(perc-lastperc >= 5): 
              print("{}% ".format(perc), end="")
              lastperc = perc
      if t > t_end: 
          print("simulation finished succesful")
          inloop = False    
 
    return np.array(res, dtype = dtype).view(np.recarray), t, status

  def finalize(self):
    # Terminate simulation in model
    self.fmiTerminate()
    self.freeModelInstance()
    
#status, state = fmu.fmiGetFMUstate()
#print("status: {}, state: {}".format(status, state))

#print("setting fmu state ...")
#fmu.fmiSetFMUstate(state)

#print(fmu.getStates())

#status, size = fmu.fmiSerializedFMUstateSize(state)
#status, vec = fmu.fmiSerializeFMUstate(state, size)

#status, state = fmu.fmiFreeFMUstate(state)
#print status, state  

#rint(fmu.getDerivatives())

#for i,j in fmu.getContinuousVariables().items():
#    print(fmu.fmiGetReal(i))

##myfmu.printvarprops()
##print(myfmu.getOutputNames())
#names=list(myfmu.getContinuousVariables().values())
##names=myfmu.getStateNames()


#simulation with generic solvers
#t_end = 10.0
#res = myfmu.simulate(dt=0.01, t_end=t_end)

#import matplotlib.pyplot as plt
#def plot():
  #for i,vals in enumerate(res[:,1:].T):
    #plt.plot(res[:,0],vals,label=names[i])
    
  #plt.legend()
  #plt.show()
  
#plot()


