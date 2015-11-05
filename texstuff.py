import sys, omg, omg.txdef, time, numpy
from PIL import Image

cache = {}

def compare_img(img1,img2):
    # do comparison, return 0 to 1 on match (1 == perfect match)
    
    if img1.size != img2.size: return 0
    ia1 = numpy.asarray(img1)
    ia2 = numpy.asarray(img2)
    
    err = numpy.sum((ia1.astype("float") - ia2.astype("float")) ** 2)
    err /= float(ia1.shape[0] * ia2.shape[1])
    return 1 / (err + 1)

def get_wad_textures(wad, ignore = None):
    # extract all textures from a wad by building from patches
    # ignore is a txdef to ignore entries from (like doom2.wad)
    txd = omg.txdef.Textures(wad.txdefs)
    output = {}
    if (ignore is not None):
        igtx = omg.txdef.Textures(ignore.txdefs)
    
    for t in txd:
        if (ignore is not None):
            if t not in igtx:
                output[t] = make_texture(wad,t,txd=txd)
        else:
            if (valid_texture(wad,t,txd)):
                output[t] = make_texture(wad,t,txd=txd)
            
    return output
    
def make_texture(wad,t,dim=None,txd=None):
    # return an Image of a texture (build from patches)
    if txd is None: 
        txd = omg.txdef.Textures(wad.txdefs)
    if (dim is None):
    
        if t in cache.keys():
            return cache[t]
        
        
        output = Image.new("RGB",(txd[t].width,txd[t].height))
        for p in txd[t].patches:
            pimg = wad.patches[p.name.upper()].to_Image()
            output.paste(pimg,(p.x,p.y))
            
        cache[t] = output
            
        return output
        
    else:
    
        if t + str(dim) in cache.keys():
            return cache[t + str(dim)]
            
        
        if t in cache.keys():
            output = cache[t]
        else:
            output = Image.new("RGB",(txd[t].width,txd[t].height))
            for p in txd[t].patches:
                pimg = wad.patches[p.name.upper()].to_Image()
                output.paste(pimg,(p.x,p.y))
            cache[t] = output
            
        cop = Image.new("RGB",dim)
        
        for i in range(dim[0]/txd[t].width):
            for j in range(dim[1]/txd[t].height):
                cop.paste(output,(i * txd[t].width,j * txd[t].height))
            
        cache[t + str(dim)] = cop
            
        return cop
    
def valid_texture(wad,name,txd):
    # check if a texture is actually made from patches in the wad
    for p in txd[name].patches:
        if p.name.upper() not in wad.patches:
            return False
    return True
    
def closest_match(img, wad):
    # find the closest matching texture in txdef to img
    m_tex = None
    m_val = -1
    txdef = omg.txdef.Textures(wad.txdefs)
    for t in txdef:
        
        if valid_texture(wad,t,txdef):
            # dimensions check
            
            
            
            if img.size[0] != txdef[t].width or img.size[1] != txdef[t].height:
                # resize image
                ti = make_texture(wad,t, txd=txdef, dim=img.size)
                v = compare_img(img,ti)
            else :
                ti = make_texture(wad,t, txd=txdef)
                v = compare_img(img,ti)
        else:
            v = 0
        
        if v > m_val:
            m_val = v
            m_tex = t
            
    return m_tex
    
def closest_flat_match(flat, flatList):
    # find the closest matching flat in wad to flat
    
    m_flat = None
    m_val = -1
    
    for name, f in flatList.iteritems():
        v = compare_img(flat,f)
        if v > m_val:
            m_val = v
            m_flat = name
            
    return m_flat
    
def get_flat_images(wad):
    # get a dictionary of image renders of flats from a wad
    
    output = {}
    
    for f in wad.flats:
        output[f] = wad.flats[f].to_Image()
        
    return output
    
def update_progress(progress):
    barLength = 10 # Modify this to change the length of the progress bar
    status = ""
    if isinstance(progress, int):
        progress = float(progress)
    if not isinstance(progress, float):
        progress = 0
        status = "error: progress var must be float\r\n"
    if progress < 0:
        progress = 0
        status = "Halt...\r\n"
    if progress >= 1:
        progress = 1
        status = "Done...\r\n"
    block = int(round(barLength*progress))
    text = "\rPercent: [{0}] {1}% {2}".format( "#"*block + "-"*(barLength-block), progress*100, status)
    sys.stdout.write(text)
    sys.stdout.flush()
    
class Benchmark:
    def __init__(self):
        self.timestr = ""
        self.starttime = time.time()
        
    def update(self,str):
        for i in range(int((time.time()-self.starttime)*1000)):
            self.timestr += str
        self.starttime = time.time()
        
    def printout(self):
        print(self.timestr)
    
def build_fake_textureset(texture_wad,names_wad,output_path,copypatches):
    # this will build a new wad, which has all the textures from
    # texture_wad in it. However, the texture1 lump will use all the
    # names from names_wad, and for each texture in names_wad, the 
    # closest matching texture from texture_wad will be used
    
    print("defining wads")
    nwad = omg.WAD(names_wad)
    twad = omg.WAD(texture_wad)
    owad = omg.WAD()
    
    # TODO: add a dummy patch
    
    
    
    print("getting texture images")
    nimg_list = get_wad_textures(nwad)
    
    owadtx = omg.txdef.Textures()
    
    print("finding matches/ building output wad")
    
    prg = 0.0
    prgmax = len(nimg_list)
    print "textures: "+str(prgmax)
    
    twadtxdef = omg.txdef.Textures(twad.txdefs)
    
    for name, t in nimg_list.iteritems():
        prg += 1
        
        match = closest_match(t,twad)
        
        # this is a name of the matching texture
        # add this to the owad, and create a texture
        
        if match not in owad.patches:
            lmp = omg.Graphic()
            lmp.from_Image(make_texture(twad,match,txd=twadtxdef))
            owad.patches[match] = lmp
        
        owadtx[name] = omg.txdef.TextureDef()
        owadtx[name].name = name
        owadtx[name].patches.append(omg.txdef.PatchDef())
        owadtx[name].patches[0].name = match
        owadtx[name].width, owadtx[name].height = owad.patches[match].dimensions
        
        update_progress(prg / prgmax)
    
    owad.txdefs = owadtx.to_lumps()
    print("\n")
    print("build flat images")
    
    tflats = get_flat_images(twad)
    
    print("workin the flats")
    
    prg = 0.0
    prgmax = len(nwad.flats)
    print "flats: "+str(prgmax)
    
    for nf in nwad.flats:
        prg += 1
        match = closest_flat_match(nwad.flats[nf].to_Image(),tflats)
        
        owad.flats[nf] = twad.flats[match].copy()
        update_progress(prg / prgmax)
    
    
    
    owad.to_file(output_path)
    
    
    
if __name__ == '__main__':
    print("running texstuff.py")
    
    starttime = time.time()
    if (len(sys.argv) > 2): doom2_path = sys.argv[2]
    output_path = "output.wad"
    if (len(sys.argv) > 3): 
        output_path = sys.argv[3]
    copypatches = True
    build_fake_textureset(sys.argv[1],doom2_path,output_path,copypatches)
    
    end = time.time()
    print "time elapsed: {}".format(end-starttime)
    
    print("its over")