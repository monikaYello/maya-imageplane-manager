import pymel.core as pm
import pymel.util as pu
import maya.cmds as cmds
import sys
import logging

"""
// Image Plane Manager
// version 1.0
// June 18, 2018
// Monika Gelbmann
// monikagelbmann@gmail.com
// www.monikagelbmann.com

	Image Plane Manager

	DESCRIPTION:
	This script lets you import and manage image planes in your scene. Main features include
	    
	    - move offset and size with sliders
	    - adjusting opacity, brightness, size with slider 
	    - retargeting between cameras in the scene
	
    PRO FEATURES
        - manipulator for free movement in relation to camera space
        
	INSTALLATION:
	a) Copy the file (mo_imageplaneManager.py) to your Maya scripts directory. 
	On Windows that is Documents/maya/20xx/scripts/

	b) Open Maya. In the Script Editor (Python), past the following code:
	import pymel.core as pm
	import mo_imageplaneManager as mo_imageplaneManager
	reload(mo_imageplaneManager)
	mo_imageplaneManager.ImagePlaneMngWindow.showUI()

	c) Hit execute (or Ctrl Enter)

	USAGE:
	1. Import new image plane. Click on 'Import New' and browse to the file

	Future Improvements/Optimzations planned:
	 - set  camera to persp as default when importing
     - on import/delete, change create command to createEdit UI, not redraw whole interface,
     - edit image plane, change size, align to left/right
     - audio import

	VERSIONS:
	1.0 - Jan 07, 2017 - Initial Release.

// Questions/comments/bugs/issues to
// monikagelbmann@gmail.com

"""

debug = False
_logger = logging.getLogger(__name__)
pro=1

class ImagePlaneMngWindow(object):
    """pymel class for Image plane manger 2.0"""

    @classmethod
    def showUI(cls):
        # classmethod to show example of class
        win=cls()
        win.create()
        return win

    def __init__(self):

        self.WINDOW_NAME = 'mo_imageplanemanager'
        self.WINDOW_TITLE = 'Image Plane Manager'
        self.WINDOW_SIZE = (350,450)


        self.listOfAlignments=['Right','Left']# list of all alignment modes
        self.refreshString='-----Refresh-----'
        self.currentImgPath=''  #setting up default  images directory
        self.currentImgPlane=False
        self.listOfImagePlanes = []
        self.listOfCameras = []

        _logger.disabled = not debug


    def numberOfImagePlanesInScene(self,*args):
        return len(self.listOfImagePlanes)

    def create(self):
        # create window "Imageplane Manager"
        ## destroy the window if it already exists
        try:
            pm.deleteUI(self.WINDOW_NAME, window=True)
        except: pass
        # draw the window
        self.WINDOW_NAME = pm.window(
            self.WINDOW_NAME,
            title=self.WINDOW_TITLE,
            width=self.WINDOW_SIZE[0], height=self.WINDOW_SIZE[1],
            sizeable = False
        )
        #main form
        _logger.debug("Creating Main Form")
        topLevelColumn = pm.columnLayout(adjustableColumn=True, columnAlign="center")

        self.mainForm = pm.formLayout(nd=100)


        #FIRST FL Manage Plane Manages control frame Layout*****************************************************
        self.modeGrpFrame=pm.frameLayout(
            label='Image Planes',
            collapsable=True,
            width=self.WINDOW_SIZE[0],
            borderStyle='etchedIn'
        )
        #attach 'Manage Plane Manages control'  group to main
        pm.formLayout(
            self.mainForm, e=True,
            attachForm=(
                  [self.modeGrpFrame,'top',16],
                  [self.modeGrpFrame,'left',6],
            )
        )

        self.modeGrpForm = pm.formLayout(nd=100)

        #Option Menu: available image planes
        self.imgplanesOptionMenu=pm.optionMenu(
            label='Image Planes',
            width=200,
            changeCommand=pm.Callback(self.on_imp_change)
        )

        # create menu item list for all image planes in scene
        _logger.debug("Creat item for all image planes in scnee")
        self.imp_option_list()

        pm.formLayout(
            self.modeGrpForm, e=True,
            attachForm=([self.imgplanesOptionMenu,'top',10],[self.imgplanesOptionMenu,'left',20])
        )
        #Del, Del All, Select Button
        self.Sel_btn = pm.button(label='Sel', width=50, command=pm.Callback(self.on_select_btn))
        self.Del_btn = pm.button(label='Del',width=50, command=pm.Callback(self.on_delete_btn))

        pm.formLayout(
            self.modeGrpForm, e=True,
            attachForm=([self.Sel_btn,'top',10]),
            attachControl=([self.Sel_btn,'left',10,self.imgplanesOptionMenu])
        )
        pm.formLayout(
            self.modeGrpForm, e=True,
            attachForm=([self.Del_btn,'top',10]),
            attachControl=([self.Del_btn,'left',10,self.Sel_btn])
        )

        _logger.debug("Import new Btn")
        #File open: import new imageplane
        self.import_btn = pm.button(label='Import New', width=self.WINDOW_SIZE[0], command=pm.Callback(self.importWindowUI))

        _logger.debug("ImportOption Menu")
        pm.formLayout(
            self.modeGrpForm, e=True,
            attachForm=([self.import_btn,'left',20]),
            attachControl=([self.import_btn,'top',5,self.imgplanesOptionMenu])
        )

        pm.setParent(self.mainForm)

        #SEC FL Edit Image Plane **************************************************************************

        _logger.debug("Framelayout: Edit Image Plane")
        self.editGrpFrame=pm.frameLayout(
            label='Edit Image Plane',
            collapsable=True,
            width=self.WINDOW_SIZE[0],
            borderStyle='etchedIn'
        )

        _logger.debug("createEditUI()")
        self.createEditUI()

        _logger.debug("attach 'Manage Plane Manages control'  group to main")
        #attach 'Manage Plane Manages control'  group to main
        pm.formLayout(
            self.mainForm, e=True,
            attachForm=([self.editGrpFrame,'left',6]),
            attachControl=([self.editGrpFrame,'top',3,self.modeGrpFrame])
        )
        pm.setParent(self.mainForm)

        _logger.debug("Camera Retarget UI")
        #THIRD Camera Retarget *************************************************************************
        self.cameraGrpFrame=pm.frameLayout(
            label='Camera Retarget',
            collapsable=True,
            width=self.WINDOW_SIZE[0],
            borderStyle='etchedIn',
            cl=True
        )

        self.createCameraUI()

        self.cameraGrpForm = pm.formLayout(nd=100)
        #self.audioGrpForm = pm.formLayout(nd=100)
        #attach 'Manage Plane Manages control'  group to main
        pm.formLayout(
            self.mainForm, e=True,
            attachForm=([self.cameraGrpFrame,'left',6]),
            attachControl=([self.cameraGrpFrame,'top',3,self.editGrpFrame])
        )
        pm.setParent(self.mainForm)

        _logger.debug("Tools UI")
        #FOURTH FL Pro-Tools *************************************************************************
        self.toolsGrpFrame=pm.frameLayout(
            label=' Pro - Tools',
            collapsable=True,
            width=self.WINDOW_SIZE[0],
            borderStyle='etchedIn'
        )

        _logger.debug("Create Tools UI")
        self.createToolsUI()

        self.toolsGrpForm = pm.formLayout(nd=100)
        #self.audioGrpForm = pm.formLayout(nd=100)
        #attach 'Manage Plane Manages control'  group to main
        pm.formLayout(
            self.mainForm, e=True,
            attachForm=([self.toolsGrpFrame,'left',6]),
            attachControl=([self.toolsGrpFrame,'top',3,self.cameraGrpFrame])
        )
        #self.modeGrpForm = pm.formLayout(nd=100)
        pm.setParent(self.mainForm)

        #FIFTH FL Audio *************************************************************************
        _logger.debug("Audio UI")
        self.audioGrpFrame=pm.frameLayout(
            label='Audio',
            collapsable=True,
            width=self.WINDOW_SIZE[0],
            borderStyle='etchedIn'
        )
        self.audioGrpForm = pm.formLayout(nd=100)
        #self.audioGrpForm = pm.formLayout(nd=100)
        #attach 'Manage Plane Manages control'  group to main
        pm.formLayout(
            self.mainForm, e=True,
            attachForm=([self.audioGrpFrame,'left',6]),
            attachControl=([self.audioGrpFrame,'top',3,self.toolsGrpFrame])
        )
        pm.showWindow()


    def createEditUI(self,*args):
        _logger.debug('createEditUI')
        self.editGrpForm = pm.columnLayout(columnOffset=("left",-1), columnAlign="left",adjustableColumn=True)
        pm.setParent(self.editGrpFrame)

        if (self.numberOfImagePlanesInScene()<=0):
            pm.text("No image planes in scene to edit", align="center")
            pm.setParent(self.editGrpForm)
        else:

            self.alignGrpForm = pm.rowLayout(nc=5)
            pm.setParent(self.alignGrpForm)
            pm.text("      Camera  ")
            pm.button(label='Select', width=120,command=pm.Callback(self.on_camselect_btn))
            pm.button(label='Look through',width=120,command=pm.Callback(self.on_camlookthrough_btn))
            pm.text(" ")
            _logger.debug('currentImgPlane[0] is %s' % self.currentImgPlane)
            # pm.checkBox( label='In all views', width=99, value=pm.imagePlane(self.currentImgPlane[0], q=1, showInAllViews=1), onc=self.on_views_change_all, ofc=self.on_views_change_current)
            pm.setParent(self.editGrpFrame)


            pm.floatSliderGrp("opacitySlider", label="Opacity", columnWidth3=(80,50,80), columnAlign3=("right","left","left"),adjustableColumn=0, field=True, fieldMinValue=0, fieldMaxValue=1, minValue=0, maxValue=1, step=0.01, cc=pm.Callback(self.on_opacity_change))
            pm.floatSliderGrp("colorOffsetSlider", label="Brightness", columnWidth3=(80,50,60), columnAlign3=("right","left","left"),adjustableColumn=0, field=True, fieldMinValue=0, fieldMaxValue=1, minValue=0, maxValue=1, step=0.01, cc=pm.Callback(self.on_colorOffset_change))


            pm.floatSliderGrp("sizeSlider", label="Size", columnWidth3=(80,60,80), columnAlign3=("right","left","left"),adjustableColumn=0, field=True, fieldMinValue=0.1, fieldMaxValue=5.0, minValue=0.1, maxValue=5.0, step=0.1, cc=pm.Callback(self.on_size_change))
            pm.floatSliderGrp("offsetXSlider", label="Offset X", columnWidth3=(80,50,80), columnAlign3=("right","left","left"),adjustableColumn=0, field=True, fieldMinValue=-1.0, fieldMaxValue=1.0, minValue=-1.0, maxValue=1.0, step=0.01, cc=pm.Callback(self.on_offsetX_change))
            pm.floatSliderGrp("offsetYSlider", label="Offset Y", columnWidth3=(80,50,80), columnAlign3=("right","left","left"),adjustableColumn=0, field=True, fieldMinValue=-1.0, fieldMaxValue=1.0, minValue=-1.0, maxValue=1.0, step=0.01, cc=pm.Callback(self.on_offsetY_change))

            #set slider values to current values
            self.updateImagePlaneEditSliders();
            pm.setParent(self.editGrpFrame)




        pm.formLayout(
            self.mainForm, e=True,
            attachForm=(
                [self.editGrpFrame,'left',6]
            ),
            attachControl=(
                [self.editGrpFrame,'top',3,self.modeGrpFrame]
            )
        )
        pm.setParent(self.mainForm)

    def createCameraUI(self, *args):
        self.cameraGrpForm =  pm.rowLayout(numberOfColumns=5, columnWidth3 =(200, 100, 200), columnAlign2=('right', 'center') )
        pm.setParent(self.cameraGrpFrame)

        if (self.numberOfImagePlanesInScene()<=0):
            pm.text("No image planes in scene to edit", align="center")
            pm.setParent(self.editGrpForm)
        else:
            #FIRST COL************************* Camera choice
            self.cameraRetargetMenu = pm.optionMenu(label='  Camera', width=110)
            self.camera_option_list(self.cameraRetargetMenu)
            #pm.setParent(self.cameraGrpForm)

            pm.button(label='Retarget',  w=20, command=pm.Callback(self.on_retarget_btn))
            #pm.setParent(self.cameraGrpForm)
            #print self.listOfCameras


    def createToolsUI(self, *args):
        self.cameraGrpForm =  pm.rowLayout(numberOfColumns=5, columnWidth3 =(200, 100, 200), columnAlign2=('right', 'center') )
        pm.setParent(self.toolsGrpFrame)

        if (self.numberOfImagePlanesInScene()<=0):
            pm.text("No image planes in scene to edit", align="center")
            pm.setParent(self.editGrpForm)
        else:
            pm.button(label='Move and Scale', en=pro, command=pm.Callback(self.on_move_btn))
            pm.button(label='Duplicate',  w=20, en=pro, command=pm.Callback(self.on_duplicate_btn))
            pm.button(label='Disconnect Mover', en=pro,  w=20, command=pm.Callback(self.on_disconnectMover_btn))
            #pm.setParent(self.cameraGrpForm)

    def importWindowUI(self,*args):

        #query main window position for alignment
        posMainWindow = pm.window(self.WINDOW_NAME, query=True, topLeftCorner  =True)

        self.importWindow = pm.window( title="Import New Image Plane", iconName='Import', widthHeight=(420, 55), topLeftCorner =posMainWindow, maximizeButton=False )
        mainLayout = pm.rowLayout(numberOfColumns=5, columnWidth3 =(20, 100, 200), columnAlign2=('right', 'center') )

       #FIRST COL************************* Camera choice
        self.cameraOptionMenu=pm.optionMenu(
            label='Camera',
            width=200,
            #changeCommand=pm.Callback(self.on_cam_change)
        )

        self.camera_option_list(self.cameraOptionMenu)


        pm.setParent(mainLayout)

         #SEC COL************************* import field
        self.ImpPathTxt=pm.textFieldButtonGrp(
            label='Import',
            text=self.currentImgPath,
            buttonLabel='Browse',
            cw3=(0, 100, 120),
            buttonCommand = pm.Callback(self.on_browse_btn)
        )
        pm.setParent(mainLayout)

        pm.showWindow()

    #find image planes in scenes -----notinuse
    @classmethod
    def findImagePlanes(self,*args):
        imgPlanes= cmds.ls(type="imagePlane")
        return imgPlanes


    ###########################
    # create transform node to move imageplane freely
    ###########################
    def createMover(self, translation=None, scale=None):
        imp = self.currentImgPlane[0]
        # create new mover or get existing
        if pm.objExists('%s_mover'%self.currentImgPlane[0]):
            mover = pm.PyNode('%s_mover'%self.currentImgPlane[0])
            pm.select(mover)
            ### TODO check if camera-imageplane has changed and if so rebuild connections
            return mover
        elif pm.getAttr('%s.sizeX'%imp, lock=True) or pm.getAttr('%s.sizeY'%imp, lock=True) or pm.getAttr('%s.offsetX'%imp, lock=True):
            sys.stderr.write('imp: Error creating Mover. Make sure imageplane %s scale and offset are not locked.'%imp)
            pm.select(imp)
            return None
        else:
            print 'imp: Creating mover for %s'%self.currentImgPlane[0]
            #mover = pm.spaceLocator(name='%s_mover'%self.currentImgPlane[0])
            mover = pm.createNode('transform', name='%s_mover'%self.currentImgPlane[0])


            #parent to camera and align to image plane
            camera = pm.listRelatives(pm.imagePlane(imp, q=1, camera=1), p=True)
            pm.parent(mover, camera)
            if translation is None:
                mover.tx.set(pm.getAttr('%s.offsetX'%imp)*10)
                mover.ty.set(pm.getAttr('%s.offsetY'%imp)*10)
            else:
                pm.xform(mover, translation = translation )

            #set distance from camera relative to focal length
            mover.tz.set(-1*(pm.getAttr('%s.focalLength'%camera[0].name())/2))

            if scale is None:
                mover.scale.set(pm.getAttr('%s.sizeX'%imp), pm.getAttr('%s.sizeY'%imp), 1)
            else:
                pm.xform(mover, scale=scale)
            mover.rotate.set([0,0,0])

            #connect imageplane to mover
            moveroffset = pm.shadingNode('multiplyDivide', asUtility=1, n='%s_moveroffset'%imp)
            moveroffset.operation.set(2)
            moveroffset.input2X.set(10)
            moveroffset.input2Y.set(10)
            mover.tx >> moveroffset.input1X
            mover.ty >> moveroffset.input1Y

            pm.connectAttr('%s.outputX'%moveroffset, '%s.offsetX'%imp, f=1)
            pm.connectAttr('%s.outputY'%moveroffset, '%s.offsetY'%imp, f=1)

            pm.connectAttr('%s.scaleX'%mover, '%s.sizeX'%imp, f=1)
            pm.connectAttr('%s.scaleY'%mover, '%s.sizeY'%imp, f=1)

            pm.select(mover)
            return mover


    def translateImageplane(self, translation, scale ):
            imp = self.currentImgPlane[0]
            try:
                pm.setAttr( '%s.offsetX'%imp, translation[0], f=1)
                pm.setAttr( '%s.offsetY'%imp, translation[1], f=1)
                pm.setAttr( '%s.sacleX'%imp, scale[0], f=1)
                pm.setAttr( '%s.sacleY'%imp, scale[1], f=1)
                return True
            except:
                print('imp: Error translateImageplane()')
                return False



    ###########################
    # fill option list with all scene image planes, sets first as active
    ###########################
    def imp_option_list(self,*args):

        del  self.listOfImagePlanes[:]
        self.imgplanesOptionMenu.clear()

        # creates a list of existing image planes and update Image Plane Option menu
        self.listOfImagePlanes =[i for i in pm.ls(type='imagePlane')]

        _logger.debug("imp_option_list: %s"%self.listOfImagePlanes)
        if len(self.listOfImagePlanes)>0:
            self.currentImgPlane = pm.imagePlane(self.listOfImagePlanes[0], query=True, name=True)
            for item in self.listOfImagePlanes:
                _logger.debug('imp is %s'%pm.imagePlane(item, query=True, name=True))
                imp = pm.imagePlane(item, query=True, name=True)
                pm.menuItem(l=imp[0],parent=self.imgplanesOptionMenu)

            # set active menu item to current image plane
            _logger.debug('Current Imageplane: %s'%self.currentImgPlane)
            pm.optionMenu(self.imgplanesOptionMenu, e=True, value="%s"%self.currentImgPlane[0])

        else:
            pm.menuItem(l="No Image Planes", parent=self.imgplanesOptionMenu)
            self.currentImgPlane = False


    def nameFromFile(self,pathname):
        try:
            fpPathObj = pu.path(pathname)
            fpFileObj = pu.path.basename(fpPathObj)
            fpFile = fpFileObj.split(".")
            fpName = fpFile[0]
            return fpName

        except:
            return "imgPlane"

    def camera_option_list(self, menu, *args):
        #clear array and optionMenu
       del self.listOfCameras[:]
       menu.clear()
       self.listOfCameras = [i for i in pm.ls(cameras=True)]

       for item in self.listOfCameras:
             ca = pm.camera(item, query=True, name=True)
             pm.menuItem(l=pm.camera(item, query=True, name=True), parent=menu)

    def get_cam(self, *args):
        currentCamItem = pm.camera(self.listOfCameras[(itemnumber-1)], query=True, name=True)
        return currentCamItem

    def duplicate_imp(self, *args):
        dupImp = pm.duplicate(self.currentImgPlane, name='%s_duplicate'%self.currentImgPlane[0])
        pm.rename(dupImp, '%s_duplicate'%self.currentImgPlane[0].split('Shape')[0])
        #pm.imagePlane(dupImp, edit=1, camera=pm.imagePlane(self.currentImgPlane, q=1, camera=1))
        print 'imp: Duplicating Imageplane %s -- %s'%(self.currentImgPlane[0], dupImp)
        return dupImp

    def disconnectMover(self, *args):
        imp = self.currentImgPlane[0]
        sizeX = pm.getAttr('%s.sizeX'%imp)
        sizeY = pm.getAttr('%s.sizeY'%imp)
        offsetX = pm.getAttr('%s.offsetX'%imp)
        offsetY = pm.getAttr('%s.offsetY'%imp)
        pm.delete(pm.listConnections('%s.sizeX'%imp))
        pm.delete(pm.listConnections('%s.offsetX'%imp))
        pm.setAttr('%s.sizeX'%imp, sizeX)
        pm.setAttr('%s.sizeY'%imp, sizeX)
        pm.setAttr('%s.offsetX'%imp, offsetX)
        pm.setAttr('%s.offsetY'%imp, offsetY)

    def updateImagePlaneEditSliders(self, *args):
        #update opacity slider
        try:
            currentOpacity = pm.getAttr(self.currentImgPlane[0] +".alphaGain")
            pm.floatSliderGrp('opacitySlider',e=True, value=currentOpacity)

            currentColorOffset = pm.getAttr(self.currentImgPlane[0] +".colorOffsetR")
            pm.floatSliderGrp('colorOffsetSlider',e=True, value=currentColorOffset)

            #currentSizeX = pm.getAttr(self.currentImgPlane[0] +".sizeX")
            #sliderMin= pm.floatSliderGrp('sizeSlider',q=True, minValue=True)
            #sliderMax= pm.floatSliderGrp('sizeSlider',q=True, maxValue=True)
            #currentSizeX = pm.util.clamp(currentSizeX, sliderMin, sliderMax)
            #pm.floatSliderGrp('sizeSlider',e=True, value=currentSizeX)

            #currentOffsetX = pm.getAttr(self.currentImgPlane[0] +".offsetX")
            #sliderMin= pm.floatSliderGrp('offsetXSlider',q=True, minValue=True)
            #sliderMax= pm.floatSliderGrp('offsetXSlider',q=True, maxValue=True)
            #3currentOffsetX = pm.util.clamp(currentOffsetX, sliderMin, sliderMax)
            #pm.floatSliderGrp('offsetXSlider',e=True, value=currentOffsetX)

            #currentOffsetY = pm.getAttr(self.currentImgPlane[0] +".offsetY")
            #sliderMin= pm.floatSliderGrp('offsetYSlider',q=True, minValue=True)
            #sliderMax= pm.floatSliderGrp('offsetYSlider',q=True, maxValue=True)
            #currentOffsetY = pm.util.clamp(currentOffsetY, sliderMin, sliderMax)
            #pm.floatSliderGrp('offsetYSlider',e=True, value=currentOffsetY)


        except:
            sys.stderr.write('Error Updating Image Plane Edit Panel. (in updateImagePlaneEditSliders)')
            return

    def on_browse_btn(self,*args):
        # Image browse button callback handler
        impFile=''
        impFile=pm.fileDialog2(fileMode=1)
        if impFile is None or len(impFile)<1: return
        else:
                print('ipm: importing new image plane %s '%cmds.file(impFile, query=True, type=True))

                currentCamera = pm.optionMenu(self.cameraOptionMenu, q=1, v=1)

                #get name for new imageplane
                impName = self.nameFromFile(pathname=impFile)

                self.currentImgPath=impFile[0]


                self.currentImgPlane = (pm.imagePlane( width=100, height=50, name=impName))[1];
                _logger.debug('Imported. file name is %s ' % impFile)

                pm.imagePlane(self.currentImgPlane, e=True, camera=currentCamera)
                _logger.debug('Set camera to  %s ' % currentCamera)
                try:
                    pm.imagePlane(self.currentImgPlane, e=True, fileName=self.currentImgPath);
                except:
                    pass
                _logger.debug('Imp file has mov is %s ' % impFile[0].rsplit('.')[-1] == "mov")
                if impFile[0].rsplit('.')[-1] == 'mov':
                    _logger.debug('Setting to .mov %s ' % self.currentImgPlane)
                    pm.setAttr('%s.type'%self.currentImgPlane, 2)

                self.imp_option_list() #update option menu
                pm.textFieldButtonGrp(self.ImpPathTxt,e=True,text=self.currentImgPath)

                #update edit image plane frame


                try:
                    #close import window
                    pm.deleteUI(self.importWindow, window=True)
                    #rebuild parent window
                    self.create()

                except:
                    sys.stderr.write('Error rebuilding Interface after image file import. Check name and file type of image.')

    def on_select_btn(self,*args):
        # Select image plane handler
        _logger.debug('ipm: selecting %s '%self.currentImgPlane)
        pm.select(self.currentImgPlane)

    def on_delete_btn(self,*args):
        # Delete image plane handler


        confirm = pm.confirmDialog( title='Delete', message='Deleting image plane %s ?'%(self.currentImgPlane), button=['Yes','No'], defaultButton='Yes', cancelButton='No', dismissString='No' )

        if confirm == 'Yes':
            print('ipm: deleting %s'%self.currentImgPlane)
            if pm.objExists('%s_mover'%self.currentImgPlane[0]):
                pm.delete('%s_mover'%self.currentImgPlane[0])
                pm.delete('%s_moveroffset'%self.currentImgPlane[0])

            pm.delete(pm.listRelatives(self.currentImgPlane, p=1))
            self.imp_option_list()
            self.create()

    def on_imp_change(self,*args):
        # image plane option menu update handler

        itemnumber = pm.optionMenu(self.imgplanesOptionMenu, q=True, select=True)
        currentImpItem = pm.imagePlane(self.listOfImagePlanes[(itemnumber-1)], query=True, name=True)

        # update currenImpPlane
        self.currentImgPlane = currentImpItem
        self.updateImagePlaneEditSliders()

    def on_opacity_change(self, *args):
        try:
            sliderValue= pm.floatSliderGrp('opacitySlider',q=True, value=True)
            pm.setAttr(self.currentImgPlane[0] +".alphaGain", sliderValue)
        except:
            sys.stderr.write('Error opacity_change.')
            return

    def on_colorOffset_change(self, *args):
        try:
            sliderValue= pm.floatSliderGrp('colorOffsetSlider',q=True, value=True)
            pm.setAttr(self.currentImgPlane[0] +".colorOffsetR", sliderValue)
            pm.setAttr(self.currentImgPlane[0] +".colorOffsetG", sliderValue)
            pm.setAttr(self.currentImgPlane[0] +".colorOffsetB", sliderValue)
        except:
            sys.stderr.write('Error colorOffset_change.')
            return

    def on_size_change(self, *args):
        self.disconnectMover()
        try:
            sliderValue = pm.floatSliderGrp('sizeSlider', q=True, value=True)
            print("onchange")
            pm.setAttr(self.currentImgPlane[0] + ".sizeX", sliderValue)

        except:
            sys.stderr.write('Error on_size_change.')
        return

    def on_offsetX_change(self, *args):
        self.disconnectMover()
        try:
            sliderValue = pm.floatSliderGrp('offsetXSlider', q=True, value=True)
            pm.setAttr(self.currentImgPlane[0] + ".offsetX", sliderValue)
        except:
            sys.stderr.write('Error offsetX_change.')
            return

    def on_offsetY_change(self, *args):
        self.disconnectMover()
        try:
            sliderValue = pm.floatSliderGrp('offsetYSlider', q=True, value=True)
            pm.setAttr(self.currentImgPlane[0] + ".offsetY", sliderValue)
        except:
            sys.stderr.write('Error offsetY_change.')
            return

    def on_move_btn(self, *args):
        self.createMover()

    def on_views_change_all(self,*args):
        pm.imagePlane(self.currentImgPlane[0], e=1, showInAllViews=1)

    def on_views_change_current(self,*args):
        pm.imagePlane(self.currentImgPlane[0], e=1, showInAllViews=0)

    def on_camselect_btn(self, *args):
        pm.select(pm.imagePlane(self.currentImgPlane, q=1, camera=1))

    def on_camlookthrough_btn(self, *args):
        pm.lookThru(pm.imagePlane(self.currentImgPlane, q=1, camera=1))

    def on_duplicate_btn(self, *args):
        dupimp = self.duplicate_imp()
        self.imp_option_list()
        self.create()
        #print 'old %s'%self.currentImgPlane
        #self.currentImgPlane = dupimp
        #print 'new %s'%dupimp


    def on_disconnectMover_btn(self, *args):
        self.disconnectMover()

    def on_retarget_btn(self, *args):
        sourcecam = pm.imagePlane(self.currentImgPlane, q=1, camera=1)
        targetcam = pm.optionMenu(self.cameraRetargetMenu, q=1, v=1)
        confirm = pm.confirmDialog( title='Confirm', message='Retargeting image plane %s from %s to %s'%(self.currentImgPlane, sourcecam, targetcam), button=['Yes','No'], defaultButton='Yes', cancelButton='No', dismissString='No' )

        if confirm == 'Yes':
            moverTranslation = None
            moverScale = None
            #retarget mover
            if pm.objExists('%s_mover'%self.currentImgPlane[0]):
                mover = '%s_mover'%self.currentImgPlane[0]
                moverTranslation = pm.xform(mover, q=1, translation=1)
                moverScale = pm.xform(mover, q=1, scale=1)
                #pm.parent(mover, pm.listRelatives(targetcam, p=1))
                #pm.xform(mover, translation=moverTranslation)
                #pm.xform(mover, scale=moverScale)
                pm.delete('%s_mover'%self.currentImgPlane[0])
                pm.delete('%s_moveroffset'%self.currentImgPlane[0])

            print 'ipm: retargeting image plane %s from %s to %s'%(self.currentImgPlane, sourcecam, targetcam)
            pm.imagePlane(self.currentImgPlane, e=1, camera=targetcam)
            #self.translateImageplane(moverTranslation, moverScale)

            self.createMover(moverTranslation, moverScale)

            return targetcam
            #except:
            #sys.stderr.write('Error retargeting image plane %s from %s to %s'%(self.currentImgPlane, sourcecam, targetcam))
        else:
            return None

    '''############ old size change methods. Replaced by mover ###########   
    def on_size_change(self, *args):
        try:
            sliderValue= pm.floatSliderGrp('sizeSlider',q=True, value=True)
            print("onchange")
            pm.setAttr(self.currentImgPlane[0] +".sizeX", sliderValue)
        except:
            sys.stderr.write('Error size_change.')
            return
       
    def on_offsetX_change(self, *args):
        try:
            sliderValue= pm.floatSliderGrp('offsetXSlider',q=True, value=True)
            pm.setAttr(self.currentImgPlane[0] +".offsetX", sliderValue)
        except:
            sys.stderr.write('Error offsetX_change.')
            return
    def on_offsetY_change(self, *args):
        try:
            sliderValue= pm.floatSliderGrp('offsetYSlider',q=True, value=True)
            pm.setAttr(self.currentImgPlane[0] +".offsetY", sliderValue)
        except:
            sys.stderr.write('Error offsetY_change.')
            return'''