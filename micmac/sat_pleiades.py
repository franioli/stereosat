import logging
import os
import shlex
import subprocess
from pathlib import Path

from easydict import EasyDict as edict
from pyproj import CRS

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("micmac")

# Add MICMAC to the PATH
MICMAC_PATH = "/opt/micmac/bin/"
os.environ["PATH"] += f":{MICMAC_PATH}"

# CHECK MICMAC INSTALLATION
if not Path(MICMAC_PATH).exists():
    logger.error("MICMAC not found in the specified path.")
    raise FileNotFoundError("MICMAC not found in the specified path.")
try:
    subprocess.run(["mm3d", "-help"], check=True)
except subprocess.CalledProcessError:
    raise RuntimeError("Unable to run MICMAC. Check installation.")


# Workflow steps
def create_sysproj_xml(epsg: int | str, fname: str = "SysPROJ.xml") -> Path:
    """Creates the SysPROJ.xml file with the specified projection information.

    Args:
        epsg (int | str): The EPSG code for the desired projection or a valid projection string
                          (PROJ.4, WKT, etc.).
        fname (str, optional): The filename for the SysPROJ.xml file. Defaults to "SysPROJ.xml".

    Returns:
        Path: The Path object representing the created file.
    """

    fname = Path(fname)

    if fname.exists():
        fname.unlink()  # Remove if it exists

    if isinstance(epsg, int):
        crs = CRS.from_epsg(epsg)
    elif isinstance(epsg, str):
        try:
            crs = CRS.from_string(epsg)
        except CRS.CRSException:
            crs = CRS.from_user_input(epsg)
    else:
        raise ValueError("EPSG must be an integer or string.")
    proj = crs.to_proj4()

    with open(fname, "w") as f:
        f.write('<?xml version="1.0" ?>\n')
        f.write("<SystemeCoord>\n")
        f.write("     <BSC>\n")
        f.write("          <TypeCoord>eTC_Proj4</TypeCoord>\n")
        f.write(f"          <AuxStr>{proj}</AuxStr>\n")
        f.write("     </BSC>\n")
        f.write("</SystemeCoord>\n")

    logger.info(f"Created SysPROJ.xml file: {fname}")

    return fname


def find_tiepoints(
    ext_im: str,
    pref_im: str = None,
    method: str = "All",
    resize: int = -1,
    export_text: bool = False,
    use_schnaps: bool = False,
    verbose: bool = True,
):
    """Compute tie points for images."""

    logger.info("Computing tie points...")

    # Check method
    if method not in ["MulScale", "All", "Line", "File", "Graph"]:
        raise ValueError(
            "Invalid method. Must be one of: MulScale, All, Line, File, Graph"
        )
    if pref_im is None:
        pref_im = ""

    cmd = f'mm3d Tapioca {method} "{pref_im}(.*).{ext_im}" {resize} ExpTxt={int(export_text)}'
    if verbose:
        print(cmd)
    ret = subprocess.run(shlex.split(cmd), capture_output=True, text=True)
    if verbose:
        print(ret.stdout)

    if use_schnaps:
        # Schnaps
        subprocess.run(["mm3d", "Schnaps", f".*{ext_im}", "MoveBadImgs", 1])

    logger.info("Tie points computed.")

    return


def convert_rpc_info(
    pref_im: str,
    ext_im: str,
    rpc_ext: str,
    deg: int,
    proj_file: str,
    verbose: bool = True,
):
    """Converts RPC information to a general bundle format."""

    # Convert RPC to general bundle format
    cmd = f'mm3d Convert2GenBundle "{pref_im}(.*).{ext_im}" "$1.{rpc_ext}" "RPC-d{deg}" Degre={deg} ChSys={proj_file}'
    # print(cmd)
    ret = subprocess.run(shlex.split(cmd), capture_output=True, text=True)
    if verbose:
        print(ret.stdout)

    maltOri_dir = f"RPC-d{deg}"

    logger.info(f"RPC information converted. Output directory: {maltOri_dir}")

    return maltOri_dir


def bundle_adjustment(
    pref_im: str,
    ext_im: str,
    deg: int,
    homol_set: str = None,
    export_text: bool = False,
    verbose: bool = True,
):
    """Performs bundle adjustment on the images."""

    logger.info("Performing bundle adjustment...")

    # Bundle adjustment
    cmd = f"mm3d Campari '{pref_im}(.*).{ext_im}') RPC-d{deg} RPC-d{deg}-adj ExpTxt={int(export_text)}"
    print(cmd)
    ret = subprocess.run(shlex.split(cmd), capture_output=True, text=True)
    print(ret.stdout)

    maltOri_dir = f"RPC-d{deg}-adj"

    logger.info(f"Bundle adjustment completed. Output directory: {maltOri_dir}")

    return maltOri_dir


def match_dense_object():
    'mm3d Malt Ortho "(.*).tif" Ori-RPC-d3-adj EXA=1 ZoomI=4 ZoomF=2 VSND=-9999 DefCor=0 Spatial=1 MaxFlow=1 DoOrtho=1 NbVI=2'

    "mm3d Tawny Ortho-MEC-Malt  RadiomEgal=0"


def match_dense_image():
    'mm3d Malt GeomImage ".*tif" Ori-RPC-d3-adj Master=IMG_PHR1B_PMS_201611031018130_SEN_5225523101_R1C1.tif SzW=1 Regul=0.1 NbVI=2 ZPas=1 ZoomI=16 ZoomF=8'
    'mm3d Malt UrbanMNE ".*tif" Ori-RPC-d3-adj DoMEC=0'
    "mm3d NuageBascule MM-Malt-Img-IMG_PHR1B_PMS_201611031018130_SEN_5225523101_R1C1/NuageImProf_STD-MALT_Etape_4.xml MEC-Malt/NuageImProf_STD-MALT_Etape_8.xml Fusion/DSM_stereo.xml"
    "mm3d SMDM Fusion/DSM_stereo.*xml"
    "mm3d Nuage2Ply Fusion/Fusion.xml Out=Fusion.ply"


def correlation_into_dem(
    prefim,
    extim,
    maltori,
    dem_init,
    gresol_set,
    gresol,
    zoom,
    imortho,
    immnt,
    doortho,
    resolortho,
):
    # ...
    pass


def merge_orthophotos(doortho):
    # ...
    pass


def post_processing(name_prefix, proj):
    # ...
    pass


# Main execution
if __name__ == "__main__":
    # Check projections, show parameters, and confirm...
    # Hard-coded values
    # Create a configuration dictionary
    args = edict(
        {
            "proj": "EPSG:32632",
            "pref_im": "IMG",
            "ext_im": "tif",
            "rpc_ext": "xml",
            "deg": 3,
            "resize": 5000,
            "export_text": True,
            "use_schnaps": False,
            "maltori": 0,
            "dem_init": "None",
            "gresol_set": False,
            "gresol": 0,
            "zoom": 2,
            "imortho": 0,
            "immnt": 0,
            "doortho": 0,
            "resolortho": 1,
        }
    )

    # MICMAC PROCESSING #################################
    sysproj = create_sysproj_xml(args.proj)

    # Extracr and match features
    find_tiepoints(
        args.pref_im,
        args.ext_im,
        method="All",
        use_schnaps=args.use_schnaps,
        resize=args.resize,
        export_text=args.export_text,
        verbose=True,
    )

    im_dir = Path("./")

    # aImgs = sorted(im_dir.glob(f"*.{args.ext_im}"))
    # aIm1 = cv2.imread(str(aImgs[0]), cv2.IMREAD_IGNORE_ORIENTATION)
    # aIm2 = cv2.imread(str(aImgs[1]), cv2.IMREAD_IGNORE_ORIENTATION)
    # TPtsVec = mm3d_utils.ImportHom(f"Homol/Pastis{aImgs[0].name}/{aImgs[1].name}.txt")
    # fig, ax = mm3d_utils.plot_images([np.asarray(aIm1), np.asarray(aIm2)])
    # mm3d_utils.plot_tiepts2(np.asarray(TPtsVec, dtype=float), ax)
    # fig.savefig("tiepoints.png")

    # Bundle adjustment
    maltOri_dir = convert_rpc_info(
        args.pref_im, args.ext_im, args.rpc_ext, args.deg, sysproj
    )
    maltOri_dir = bundle_adjustment(args.pref_im, args.ext_im, args.deg)

    # Correlation into DEM

    print("Done.")
