#TH from flask import Flask, request, redirect, url_for, jsonify
from flask import Flask, request, Response, redirect, url_for, jsonify
from werkzeug import secure_filename
import numpy as np
from EMAN2 import EMData, EMNumPy
from powerspec import prepare_ideal_power_spectrum_from_layer_lines,compute_Bfactor_mask,make_combined_sim_real_powerspectrum
from layerline import generate_layerline_bessel_pairs_from_rise_and_rotation
from plot import plot_power_spectra
from bokeh.embed import components
#TH
from flask_login import current_user
from bokeh.util import session_id
#TH END
from functools import wraps
import sys
import os
import time
###TH https://stackoverflow.com/questions/12118355/secure-static-files-with-flask
class SecuredStaticFlask(Flask):
    def send_static_file(self, filename):
        # Get user from session
#	user = current_user
#        if user.is_authenticated():
	    auth = request.authorization
	    #print("AUTH:"+auth.username)
            if not auth or not check_auth(auth.username, auth.password):
                return authenticate()
            return super(SecuredStaticFlask, self).send_static_file(filename)
#        else:
#            abort(403) 
            # Or 401 (or 404), whatever is most appropriate for your situation
###TH END
# Make new Flask Application Object
#TH app = Flask(__name__, static_folder=sys.argv[4].rstrip("/"))
app = SecuredStaticFlask(__name__, static_url_path="/hspss",static_folder=sys.argv[4].rstrip("/"))

# This is the path to the upload directory
app.config['UPLOAD_FOLDER'] = sys.argv[3]
# These are the extension that we are accepting to be uploaded
app.config['ALLOWED_EXTENSIONS'] = set(['hdf', 'mrc', 'pgm'])

### TH authentification acc to: http://flask.pocoo.org/snippets/8/
def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == 'test' and password == 'S@chseEMBL'

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated
###
# For a given file, return whether it's an allowed type or not
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

#Serves index.html Page
@app.route('/')
@requires_auth
def index():
    return redirect(url_for('static', filename='index.html'))
    #return redirect(url_for('hspss', filename='index.html'))

###TH
@app.route('/hspss')
@requires_auth
def hspss():
    return redirect(url_for('static', filename='index.html'))
    #return redirect(url_for('hspss', filename='index.html'))

###TH END

# Route that will process the file upload
@app.route('/upload', methods=['POST'])
@requires_auth
def upload():
    rotation = request.form['rotation']
    rise = request.form['rise']
    pixelsize = request.form['pixelsize']
    highres = request.form['highres']
    lowres = request.form['lowres']
    powersize = request.form['powersize']
    helixwidth = request.form['helixwidth']
    bfactor = request.form['bfactor']
    sym = request.form['sym']

    checker = [[rotation, 'Rotation', 1.0, 359.0],
               [rise, 'Rise', 1.0, 300.0],
               [pixelsize, 'Pixelsize', 0.25, 20.0],
               [highres, 'High Res Cutoff', 2.0, 40.0],
               [lowres, 'Low Res Cutoff', 100.0, 1000.0],
               [powersize, 'Details Simulation in Pixel', 50.0, 1500.0],
               [helixwidth, 'Helix Width', 5.0, 500.0],
               [bfactor, 'B-Factor', 1.0, 100000.0],
               [sym, 'Symmetry', 1.0, 16.0]]

    for check in checker:
        allowed, msg = allowed_range(*check)
        if allowed == False:
            return jsonify({"parameters": msg,  "label": 'ParameterError'})

    if float(highres)>=float(lowres):
        return jsonify({"parameters": 'High Res Cutoff must be smaller than Low Res cutoff',
                        "label": 'ParameterError'})

    try:
        file = request.files['file']
        filename = secure_filename(file.filename)
        if allowed_file(filename):
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            raise TypeError('File must have correct format.')
    except:
        filename = 'None'

    return redirect(url_for('uploaded_file',filename=filename,
                            pixelsize=pixelsize, rise=rise, rotation=rotation, highres=highres,
                            lowres = lowres, powersize=powersize, helixwidth=helixwidth,
                            bfactor=bfactor, sym=sym))


def allowed_range(parameter, name, parmin, parmax):
    # This will check if input parameters by client are allowed
    parameter = float(parameter)
    if parameter >= parmin and parameter <=parmax:
        return [True, None]
    else:
        return [False, 'We had to restrict the parameter range such that not too much load is on the server.<br>'+\
                       'Parameter Error: %s must be between %.2f and %.2f'%(name, parmin, parmax)]


# Route that will return plot to the client
@app.route("/upload/<filename>/<pixelsize>/<rise>/<rotation>/<highres>/<lowres>/<powersize>/<helixwidth>/<bfactor>/<sym>")
@requires_auth
def uploaded_file(filename, pixelsize, rise, rotation, highres, lowres, powersize, helixwidth, bfactor, sym):
    if filename!='None':
        im = EMData()
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        im.read_image(str(path) , 0)
        im = np.copy(EMNumPy.em2numpy(im))
        os.remove(str(path))
        im_coll = im.mean(1)
        justsim = False
    #im = zoom(im, 0.5, order=1)
    else:
        justsim = True

    start_time = time.time()

    # Make inputs the right datatype
    bfactor = float(bfactor)
    high_resolution_cutoff = float(highres)
    low_resolution_cutoff=float(lowres)
    power_size = int(powersize)
    #power_size = int(np.ceil(int(powersize) / 2.) * 2.0 + 1.0) # To nearest uneven number
    pixelsize=float(pixelsize)
    pixelsize_simulation = high_resolution_cutoff/2.0
    rise = float(rise)
    rotation = float(rotation)
    nyquist = 1 / (2 * pixelsize)
    nyquist_simulation = 1 / (2 * pixelsize_simulation)
    width = float(helixwidth)
    para = (rise, rotation)
    sym = int(sym)




    layerline_bessel_pairs = generate_layerline_bessel_pairs_from_rise_and_rotation(para, sym, width, pixelsize_simulation, low_resolution_cutoff,
                                                                                    high_resolution_cutoff, 0)
    im_theo = prepare_ideal_power_spectrum_from_layer_lines(layerline_bessel_pairs, width,
                                                            power_size, pixelsize_simulation)
    falloff = compute_Bfactor_mask(power_size, pixelsize_simulation, bfactor)
    im_theo = im_theo * falloff
    im_theo_coll = im_theo.mean(1)


    if justsim:
        l1 = plot_power_spectra(layerline_bessel_pairs, im_theo, im_theo_coll,
                                nyquist, nyquist_simulation)
        script1, div1 = components(l1)
        script2, div2 = '', ''
    else:
        l1 = plot_power_spectra(layerline_bessel_pairs, im_theo, im_theo_coll,
                               nyquist, nyquist_simulation, im, im_coll)
        im_theo_like_upload = prepare_ideal_power_spectrum_from_layer_lines(layerline_bessel_pairs, width,
                                                                im.shape[0], pixelsize)
        combi = make_combined_sim_real_powerspectrum(im, im_theo_like_upload)
        falloff2 = compute_Bfactor_mask(im.shape[0], pixelsize, bfactor)
        combi *= falloff2
        combi_coll = combi.mean(1)
        l2 = plot_power_spectra(layerline_bessel_pairs, combi, combi_coll,
                                nyquist, nyquist)
        script1, div1 = components(l1)
        script2, div2 = components(l2)


    label = u'Sim:%.2f\u212B;%.2f\u00B0'%(rise, rotation)+(not justsim)*'+Upload'

    units_per_turn = 360.0 / rotation
    pitch = rise * units_per_turn

    time_elapsed = (time.time() - start_time)

    parameterlist = [['Rise', u'%.3f \u212B'%rise],
                     ['Rotation', u'%.3f \u00B0'%rotation],
                     ['Pitch', u'%.3f \u212B'%pitch],
                     ['Units per Turn', u'%.3f'%units_per_turn],
                     ['Helix Width', u'%s \u212B'%width],
                     ['B-Factor', u'%.1f \u212B\u00B2'%bfactor],
                     ['High Resolution Cutoff', u'%s \u212B'%high_resolution_cutoff],
                     ['Low Resolution Cutoff', u'%s \u212B'%low_resolution_cutoff],
                     ['Helix Rotational Symmetry', u'%s' % sym],
                     ['Number of Pixel in Simulation', u'%s'%power_size],
                     ['Time Elapsed', u'%.3f s'%time_elapsed]]

    parameter_html = u'<table><tr><th>Parameter</th><th>Input Value</th></tr><tr>'
    for p in parameterlist:
        parameter_html += u'<td>%s</td><td>%s</td></tr>'%(p[0],p[1])
    parameter_html += u'</table>'

    layerlines_html = u'<table><tr><th>Position \u212B</th><th>Position 1/\u212B</th><th>Bessel Order</th></tr><tr>'
    for l in layerline_bessel_pairs:
        layerlines_html += u'<td>%.4f</td><td>%.4f</td><td>%s</td></tr>' % (1.0/l[0], l[0], l[1])
    layerlines_html += u'</table>'


    # Return the webpage
    return jsonify({"script1":script1, "div1":div1, "script2":script2, "div2":div2,
                    "label":label, "parameters": parameter_html, "justsim":justsim, "layerlines":layerlines_html})



if __name__ == "__main__":
    if len(sys.argv)==5:
        app.run(host=sys.argv[1], port=sys.argv[2], threaded=True)
    else:
        print("Please specify IP address, Port, Upload Folder, Static Folder in command line! e.g. python server.py 192.168.178.170 8080 /foo/upload_folder/ /foo/static/")
