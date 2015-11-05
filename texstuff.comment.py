import sys, omg, omg.txdef, time, numpy
from PIL import Image

cache = {}  # assign {} to cache

def compare_img(img1,img2):
# do comparison, return 0 to 1 on match (1 == perfect match)

    if img1.size != img2.size: return 0
    ia1 = numpy.asarray(img1)  # assign numpy.asarray(img1) to ia1
    ia2 = numpy.asarray(img2)  # assign numpy.asarray(img2) to ia2
    
    err = numpy.sum((ia1.astype("float") - ia2.astype("float")) ** 2)  # assign numpy.sum((ia1.astype("float") - ia2.astype("float")) ** 2) to err
    err /= float(ia1.shape[0] * ia2.shape[1])  # divide err by float(ia1.shape[0] * ia2.shape[1])
    return 1 / (err + 1)
    
def get_wad_textures(wad, ignore = None):
# extract all textures from a wad by building from patches
# ignore is a txdef to ignore entries from (like doom2.wad)
    txd = omg.txdef.Textures(wad.txdefs)  # assign omg.txdef.Textures(wad.txdefs) to txd
    output = {}  # assign {} to output
    if (ignore is not None):
        igtx = omg.txdef.Textures(ignore.txdefs)  # assign omg.txdef.Textures(ignore.txdefs) to igtx
        
    for t in txd:
        if (ignore is not None):
            if t not in igtx:
                output[t] = make_texture(wad,t)  # assign make_texture(wad,t) to output[t]
        else:
            if (valid_texture(wad,t,txd)):
                output[t] = make_texture(wad,t)  # assign make_texture(wad,t) to output[t]
                
    return output
    
def make_texture(wad,t):
# return an Image of a texture (build from patches)

    if t in cache.keys():
        return cache[t]
        
    txd = omg.txdef.Textures(wad.txdefs)  # assign omg.txdef.Textures(wad.txdefs) to txd
    output = Image.new("RGB",(txd[t].width,txd[t].height))  # assign Image.new("RGB",(txd[t].width,txd[t].height)) to output
    for p in txd[t].patches:
        pimg = wad.patches[p.name.upper()].to_Image()  # assign wad.patches[p.name.upper()].to_Image() to pimg
        output.paste(pimg,(p.x,p.y))
        
    cache[t] = output  # assign output to cache[t]
    
    return output
    
def valid_texture(wad,name,txd):
# check if a texture is actually made from patches in the wad
    for p in txd[name].patches:
        if p.name.upper() not in wad.patches:
            return False
    return True
    
def closest_match(img, wad):
# find the closest matching texture in txdef to img
    m_tex = None  # assign None to m_tex
    m_val = -1  # assign -1 to m_val
    txdef = omg.txdef.Textures(wad.txdefs)  # assign omg.txdef.Textures(wad.txdefs) to txdef
    for t in txdef:
    
        if valid_texture(wad,t,txdef):
        # dimensions check
        
            if img.size[0] != txdef[t].width or img.size[1] != txdef[t].height:
                v = 0  # assign 0 to v
            else :
                ti = make_texture(wad,t)  # assign make_texture(wad,t) to ti
                v = compare_img(img,ti)  # assign compare_img(img,ti) to v
        else:
            v = 0  # assign 0 to v
            
        if v > m_val:
            m_val = v  # assign v to m_val
            m_tex = t  # assign t to m_tex
            
    return m_tex
    
def update_progress(progress):
    barLength = 10 # Modify this to change the length of the progress bar
    status = ""  # assign "" to status
    if isinstance(progress, int):
        progress = float(progress)  # assign float(progress) to progress
    if not isinstance(progress, float):
        progress = 0  # assign 0 to progress
        status = "error: progress var must be float\r\n"  # assign "error: progress var must be float\r\n" to status
    if progress < 0:
        progress = 0  # assign 0 to progress
        status = "Halt...\r\n"  # assign "Halt...\r\n" to status
    if progress >= 1:
        progress = 1  # assign 1 to progress
        status = "Done...\r\n"  # assign "Done...\r\n" to status
    block = int(round(barLength*progress))  # assign int(round(barLength*progress)) to block
    text = "\rPercent: [{0}] {1}% {2}".format( "#"*block + "-"*(barLength-block), progress*100, status)  # assign "\rPercent: [{0}] {1}% {2}".format( "#"*block + "-"*(barLength-block), progress*100, status) to text
    sys.stdout.write(text)  # note that due to buffering, flush() or close() may be needed before
    sys.stdout.flush()
    
class Benchmark:
    def __init__(self):
        self.timestr = ""  # assign "" to self.timestr
        self.starttime = time.time()  # assign time.time() to self.starttime
        
    def update(self,str):
        for i in range(int((time.time()-self.starttime)*1000)):
            self.timestr += str  # add str to self.timestr
        self.starttime = time.time()  # assign time.time() to self.starttime
        
    def printout(self):
        print(self.timestr)  # prints the values to a stream, or to sys.stdout by default
        
def build_fake_textureset(texture_wad,names_wad,output_path,copypatches):
# this will build a new wad, which has all the textures from
# texture_wad in it. However, the texture1 lump will use all the
# names from names_wad, and for each texture in names_wad, the 
# closest matching texture from texture_wad will be used

    print("defining wads")  # prints the values to a stream, or to sys.stdout by default
    nwad = omg.WAD(names_wad)  # assign omg.WAD(names_wad) to nwad
    twad = omg.WAD(texture_wad)  # assign omg.WAD(texture_wad) to twad
    owad = omg.WAD()  # assign omg.WAD() to owad
    
    print("getting texture images")  # prints the values to a stream, or to sys.stdout by default
    nimg_list = get_wad_textures(nwad)  # assign get_wad_textures(nwad) to nimg_list
    
    owadtx = omg.txdef.Textures()  # assign omg.txdef.Textures() to owadtx
    
    print("finding matches/ building output wad")  # prints the values to a stream, or to sys.stdout by default
    
    prg = 0.0  # assign 0.0 to prg
    prgmax = len(nimg_list)  # assign len(nimg_list) to prgmax
    print prgmax
    
    for name, t in nimg_list.iteritems():
        prg += 1  # add 1 to prg
        
        match = closest_match(t,twad)  # assign closest_match(t,twad) to match
        
        # this is a name of the matching texture
        # add this to the owad, and create a texture
        
        if copypatches is True:
            if match not in owad.data:
                lmp = omg.Graphic()  # assign omg.Graphic() to lmp
                lmp.from_Image(make_texture(twad,match))
                owad.data[match] = lmp  # assign lmp to owad.data[match]
                
        owadtx[name] = omg.txdef.TextureDef()  # assign omg.txdef.TextureDef() to owadtx[name]
        owadtx[name].name = name  # assign name to owadtx[name].name
        owadtx[name].patches.append(omg.txdef.PatchDef())
        owadtx[name].patches[0].name = match  # assign match to owadtx[name].patches[0].name
        if copypatches is True:
            owadtx[name].width, owadtx[name].height = owad.data[match].dimensions  # assign owad.data[match].dimensions to owadtx[name].width, owadtx[name].height
            
        update_progress(prg / prgmax)
        
    owad.txdefs = owadtx.to_lumps()  # assign owadtx.to_lumps() to owad.txdefs
    
    owad.to_file(output_path)
    
    
    
if __name__ == '__main__':
    print("running texstuff.py")  # prints the values to a stream, or to sys.stdout by default
    
    starttime = time.time()  # assign time.time() to starttime
    if (len(sys.argv) > 2): doom2_path = sys.argv[2]
    output_path = "output.wad"  # assign "output.wad" to output_path
    if (len(sys.argv) > 3):
        output_path = sys.argv[3]  # assign sys.argv[3] to output_path
    copypatches = False  # assign False to copypatches
    if (len(sys.argv) > 4):
        if "-p" in sys.argv:
            copypatches = True  # assign True to copypatches
    build_fake_textureset(sys.argv[1],doom2_path,"output2.wad",copypatches)
    
    end = time.time()  # assign time.time() to end
    print "time elapsed: {}".format(end-starttime)
    
