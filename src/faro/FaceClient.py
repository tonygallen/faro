#! /usr/bin/env python

'''
MIT License

Copyright 2019 Oak Ridge National Laboratory

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Created on Jul 18, 2018

@author: bolme
'''

import faro.proto.face_service_pb2_grpc as fs
import grpc
import faro.proto.proto_types as pt
import faro.proto.face_service_pb2 as fsd
import time
import faro
try:
    from zeroconf import ServiceInfo,Zeroconf,ServiceBrowser
except:
    Zeroconf = None
    print('Warning: could not load Bonjour services. This worker will not be broadcast. To enable broadcasting capabilities, perform `pip install zeroconf`')


class ClientOptions(object):
    pass



DEFAULT_MAX_ASYNC = 4


def getDefaultClientOptions():
    '''
    Create an object containing good default options for the client.
    '''
    
    options = ClientOptions()
    options.max_async = 4
    options.port = 'localhost:50030'
    options.verbose = False
    options.quality=95
    options.compression='uint8'
    options.service_name=None
    
    return options


class FaceClient(object):
    '''
    
    '''
    def __init__(self,options,max_message_length=-1,timeout=None):
        
        self.options = options

        channel_options = [("grpc.max_send_message_length", max_message_length),
                           ("grpc.max_receive_message_length", max_message_length)]

        self.max_async_jobs = DEFAULT_MAX_ASYNC # TODO: This needs to come from options
        
        try:
            self.max_async_jobs = options.max_async
        except:
            pass
        
        self.max_async_jobs = max(self.max_async_jobs,1)
        self.async_sleep_time = 0.001
        self.running_async_jobs = []

        port = None
        if options.service_name is not None:
            port = self.getAddressByName(options, options.service_name)
        if port is None:
            port = options.port
        channel = grpc.insecure_channel(port,
                                        options=channel_options)
        self.service_stub = fs.FaceRecognitionStub(channel)
        #channel = grpc.insecure_channel(options.rec_port,
        #                                options=channel_options)
        #self.rec_stub = fs.FaceRecognitionStub(channel)
        self.is_ready,self.info = self.status(False,timeout=timeout)
        if options.verbose:
            print (self.status)

    def getAddressByName(self,options,name):
        self.zeroconf = Zeroconf()
        import faro.command_line as command_line
        serviceList = command_line.getRunningWorkers(options)
        for service in serviceList:
            if service['Name'] == name:
                return service['address']+":"+str(service['port'])
        else:
            print('Found no running services named \"',name,'\"')
            return None

    def waitOnResults(self):
        while len(self.running_async_jobs) >= self.max_async_jobs:
            self.running_async_jobs = list(filter(lambda x: x.running(),self.running_async_jobs))
            if len(self.running_async_jobs) >= self.max_async_jobs: 
                time.sleep(self.async_sleep_time)


    def detect(self,im,best=False,threshold=None,min_size=None, run_async=False,source=None,subject_id=None,frame=None,downsample=0):
        request = fsd.DetectRequest()
        try:
            request.image.CopyFrom( pt.image_np2proto(im, compression=self.options.compression, quality=self.options.quality))
        except:
            request.image.CopyFrom( pt.image_np2proto(im.asOpenCV2()[:,:,::-1], compression=self.options.compression, quality=self.options.quality))
            
        # Setup the source and subject information.
        request.source='UNKNOWN_SOURCE'
        request.subject_id='UNKNOWN_SUBJECT'
        if source is not None:
            request.source=source
        if frame is not None:
            request.frame=frame
        if subject_id is not None:
            request.subject_id=subject_id

        
        request.detect_options.best=best
        request.detect_options.downsample=downsample
        
        if threshold == None:
            request.detect_options.threshold = self.info.detection_threshold
        else: 
            request.detect_options.threshold = float(threshold)
            
        if run_async == False:
            face_records = self.service_stub.detect(request,None)
        elif run_async == True:
            self.waitOnResults()
            face_records = self.service_stub.detect.future(request,None)
            self.running_async_jobs.append(face_records)
        else:
            raise ValueError("Unexpected run_async value: %s"%(run_async,))
                                
        return face_records
    
    def extract(self, im, face_records, run_async=False):
        request = fsd.ExtractRequest()
        try:
            request.image.CopyFrom( pt.image_np2proto(im, compression=self.options.compression, quality=self.options.quality))
        except:
            request.image.CopyFrom( pt.image_np2proto(im.asOpenCV2()[:,:,::-1], compression=self.options.compression, quality=self.options.quality))
            
        request.records.CopyFrom(face_records)
        
        if run_async == False:
            face_records = self.service_stub.extract(request,None)
        elif run_async == True:
            self.waitOnResults()
            face_records = self.service_stub.extract.future(request,None)
            self.running_async_jobs.append(face_records)
        else:
            raise ValueError("Unexpected run_async value: %s"%(run_async,))
        
        return face_records

    def detectExtract(self,im,best=False,threshold=None,min_size=None, run_async=False,source=None,subject_id=None,frame=None,downsample=0):
        request = fsd.DetectExtractRequest()
        request.detect_request.CopyFrom( fsd.DetectRequest() )
        request.extract_request.CopyFrom( fsd.ExtractRequest() )

        try:
            request.detect_request.image.CopyFrom( pt.image_np2proto(im, compression=self.options.compression, quality=self.options.quality))
        except:
            request.detect_request.image.CopyFrom( pt.image_np2proto(im.asOpenCV2()[:,:,::-1], compression=self.options.compression, quality=self.options.quality))
            

        # Setup the source and subject information.
        request.detect_request.source='UNKNOWN_SOURCE'
        request.detect_request.subject_id='UNKNOWN_SUBJECT'
        if source is not None:
            request.detect_request.source=source
        if frame is not None:
            request.detect_request.frame=frame
        if subject_id is not None:
            request.detect_request.subject_id=subject_id
            
            
        request.detect_request.detect_options.best=best
        request.detect_request.detect_options.downsample=downsample
        
        if threshold == None:
            request.detect_request.detect_options.threshold = self.info.detection_threshold
        else: 
            request.detect_request.detect_options.threshold = float(threshold)
            
            
            
        if run_async == False:
            face_records = self.service_stub.detectExtract(request,None)
        elif run_async == True:
            self.waitOnResults()
            face_records = self.service_stub.detectExtract.future(request,None)
            self.running_async_jobs.append(face_records)
        else:
            raise ValueError("Unexpected run_async value: %s"%(run_async,))
        return face_records
    
    
    
    def detectExtractEnroll(self,im,enroll_gallery='default',best=False,threshold=None,min_size=None, run_async=False,source=None,
                            subject_id=None,subject_name=None,frame=None,downsample=0):
        request = fsd.DetectExtractEnrollRequest()
        request.detect_request.CopyFrom( fsd.DetectRequest() )
        request.extract_request.CopyFrom( fsd.ExtractRequest() )
        request.enroll_request.CopyFrom( fsd.EnrollRequest() )

        try:
            request.detect_request.image.CopyFrom( pt.image_np2proto(im, compression=self.options.compression, quality=self.options.quality))
        except:
            request.detect_request.image.CopyFrom( pt.image_np2proto(im.asOpenCV2()[:,:,::-1], compression=self.options.compression, quality=self.options.quality))
            
        request.enroll_request.enroll_gallery = enroll_gallery

        # Setup the source and subject information.
        request.detect_request.source='UNKNOWN_SOURCE'
        request.detect_request.subject_id='UNKNOWN_SUBJECT'
        if source is not None:
            request.detect_request.source=source
        if frame is not None:
            request.detect_request.frame=frame
        if subject_id is not None:
            request.detect_request.subject_id=subject_id
        if subject_name is not None:
            request.detect_request.subject_name=subject_name
            
            
        request.detect_request.detect_options.best=best
        request.detect_request.detect_options.downsample=downsample
        
        if threshold == None:
            request.detect_request.detect_options.threshold = self.info.detection_threshold
        else: 
            request.detect_request.detect_options.threshold = float(threshold)
            
            
            
        if run_async == False:
            face_records = self.service_stub.detectExtractEnroll(request,None)
        elif run_async == True:
            self.waitOnResults()
            face_records = self.service_stub.detectExtractEnroll.future(request,None)
            self.running_async_jobs.append(face_records)
        else:
            raise ValueError("Unexpected run_async value: %s"%(run_async,))
                                
        return face_records
    
    
    def detectExtractSearch(self,im,search_gallery='default',max_results=3,search_threshold=None,best=False,
                                threshold=None,min_size=None, run_async=False,source=None,subject_id=None,
                                frame=None,downsample=0):
        request = fsd.DetectExtractSearchRequest()
        request.detect_request.CopyFrom( fsd.DetectRequest() )
        request.extract_request.CopyFrom( fsd.ExtractRequest() )
        request.search_request.CopyFrom( fsd.SearchRequest() )

        try:
            request.detect_request.image.CopyFrom( pt.image_np2proto(im, compression=self.options.compression, quality=self.options.quality))
        except:
            request.detect_request.image.CopyFrom( pt.image_np2proto(im.asOpenCV2()[:,:,::-1], compression=self.options.compression, quality=self.options.quality))
            
        request.search_request.search_gallery = search_gallery
        request.search_request.max_results=max_results
        
        if search_threshold is None:
            search_threshold = self.match_threshold
            
        request.search_request.threshold = search_threshold


        # Setup the source and subject information.
        request.detect_request.source='UNKNOWN_SOURCE'
        request.detect_request.subject_id='UNKNOWN_SUBJECT'
        if source is not None:
            request.detect_request.source=source
        if frame is not None:
            request.detect_request.frame=frame
        if subject_id is not None:
            request.detect_request.subject_id=subject_id
            
            
        request.detect_request.detect_options.best=best
        request.detect_request.detect_options.downsample=downsample
        
        if threshold == None:
            request.detect_request.detect_options.threshold = self.info.detection_threshold
        else: 
            request.detect_request.detect_options.threshold = float(threshold)
            
            
            
        if run_async == False:
            face_records = self.service_stub.detectExtractSearch(request,None)
        elif run_async == True:
            self.waitOnResults()
            face_records = self.service_stub.detectExtractSearch.future(request,None)
            self.running_async_jobs.append(face_records)
        else:
            raise ValueError("Unexpected run_async value: %s"%(run_async,))
                                
        return face_records
    
    
    def enroll(self,faces, enroll_gallery, subject_id=None, subject_name=None, run_async=False,**kwargs):
        request = fsd.EnrollRequest()
        request.enroll_gallery = enroll_gallery  
        if subject_id is not None:
            for face in faces.face_records:
                face.subject_id = subject_id
        if subject_name is not None:
            for face in faces.face_records:
                face.name = subject_name
                
        request.records.CopyFrom(faces)
    
        if run_async == False:
            error = self.service_stub.enroll(request,None)
        elif run_async == True:
            self.waitOnResults()
            error = self.service_stub.enroll.future(request,None)
            self.running_async_jobs.append(error)
        else:
            raise ValueError("Unexpected run_async value: %s"%(run_async,))

        return error
        
        
    def galleryList(self):
        '''Get a list of the galleries'''
        
        request = fsd.GalleryListRequest()
        
        result = self.service_stub.galleryList(request)
        
        return result
    

    def galleryDelete(self, gallery_name):
        '''Get a list of the galleries'''
        
        request = fsd.GalleryDeleteRequest()
        
        request.gallery_name = gallery_name

        result = self.service_stub.galleryDelete(request)
        
        return result
    

    def faceList(self,gallery_name):
        '''Get a list faces in a gallery'''
        
        request = fsd.EnrollmentListRequest()
        request.gallery_name = gallery_name
        result = self.service_stub.enrollmentList(request)
        
        return result


    def subjectDelete(self,gallery_name,subject_id):
        '''Get a list faces in a gallery'''
        
        request = fsd.EnrollmentDeleteRequest()
        request.gallery_name = gallery_name
        request.subject_id = subject_id
        result = self.service_stub.subjectDelete(request)
        
        return result


    def search(self, faces, search_gallery, max_results=3, search_threshold=None, run_async=False, **kwargs):
        request = fsd.SearchRequest()
        
        request.probes.CopyFrom(faces)
        request.search_gallery = search_gallery
        request.max_results=max_results
        
        if search_threshold is not None:
            request.threshold=search_threshold
            
        if run_async == False:
            error = self.service_stub.search(request,None)
        elif run_async == True:
            self.waitOnResults()
            error = self.service_stub.search.future(request,None)
            self.running_async_jobs.append(error)
        else:
            raise ValueError("Unexpected run_async value: %s"%(run_async,))

        return error
        

    def score(self,probe,gallery):
        '''
        '''
        request = fsd.ScoreRequest()
        
        # Copy the templates into the request
        for face_rec in probe:
            request.template_probes.templates.add().CopyFrom(face_rec.template)
        for face_rec in gallery:
            request.template_gallery.templates.add().CopyFrom(face_rec.template)
        
        # Run the computation on the server
        dist_mat = self.service_stub.score(request,None)
        return pt.matrix_proto2np(dist_mat)

    def generateMatchDistribution(self,gallery_name):
        request = fsd.EnrollmentListRequest()
        request.gallery_name = gallery_name
        dist_mat = self.service_stub.generateMatchDistribution(request)
        return pt.matrix_proto2np(dist_mat)
        
    def echo(self,mat):
        '''
        '''
        request = pt.matrix_np2proto(mat)
        
        
        # Run the computation on the server
        dist_mat = self.service_stub.echo(request,None)
        
        return pt.matrix_proto2np(dist_mat)


    def status(self,verbose=False,timeout=None):
        request = fsd.FaceStatusRequest()
        iserror = False
        try:
            status_message = self.service_stub.status(request,timeout=timeout)
        except Exception as e:
            iserror = True
            status_message = "cannot connect"
            if verbose:
                status_message = "cannot connect:" + str(e)
        if verbose:
            print(type(status_message),status_message)
        if not iserror:
            self.match_threshold = status_message.match_threshold

            return status_message.status == fsd.READY, status_message
        else:
            return False, status_message
    
    def trainFromGallery(self,gallery_name):
        request = fsd.EnrollmentListRequest()
        request.gallery_name = gallery_name
        result = self.service_stub.trainFromGallery(request)
        return result
    
    
    
if __name__ == '__main__':
    raise NotImplementedError("This main function has been removed. Please use: 'python -m faro ...'")
        


