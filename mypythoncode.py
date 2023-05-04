import argparse
import base64
import json
import os
import yaml

from jinja2 import Environment, FileSystemLoader
from subprocess import Popen, PIPE

OutputDir = os.path.realpath('Outputs')
j2Dir = os.path.realpath('j2_templates')
OutputJ2 = 'j2data.j2'
OutputSCJ2 = 'sdata.j2'

class MyPythonCode(object):
    def __init__(
            self, myjsonfile):
        self._load_data(myjsonfile)
        self.my_output_file = (f'{OutputDir}/output_file.json')
        self.decrypt_file = (f'{OutputDir}/decrypt_file.yaml')
        self.my_output_scfile = (f'{OutputDir}/output_scfile.json')
    
    def _run_shell(self, cmd, use_shell=False):
        proc = Popen(cmd, shell=use_shell, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        proc.wait()
        out, err = proc.communicate()
        if proc.returncode != 0:
            raise Exception(err.decode())
        return out.decode().replace('\n', '')
    
    def _load_data(self, myjsonfile):
        try:
            with open(myjsonfile) as myjs:
                self.myjs = json.load(myjs)
        except Exception as e:
            print("Failed to load data")
            print(f"{e}")

 # jsonargs === j2_args

    def _loadj2(self, j2file, jsonargs):
        try:
            j2_loader = FileSystemLoader(j2Dir)
            jenv = Environment(loader=j2_loader)
            j2temp = jenv.get_template(j2file)
            j2data = j2temp.render(jsonargs)
            j2yaml = yaml.safe_load(j2data)
            return j2yaml
        except Exception as e:
            print(f"j2 rendering failed '{j2file}'!")
            print(f'{e}')
            raise e

    def _generate_output_file(self):
        jsonargs = {
            'myjsondata': self.myjsonfile}
        output_file_data = self._loadj2(OutputJ2, jsonargs)
        output_file_data = output_file_data['myj2data']
        try:
            with open(self.my_output_file, 'r') as json_in_file:
                op_jsondata =  json.load(json_in_file)
            for j2_key, j2_val in output_file_data.items():
                op_jsondata['myj2data'][j2_key] = [j2_val]
            with open(self.my_output_file, 'w') as json_out_file:
                json.dump(op_jsondata, json_out_file, indent=4)
        except Exception as e:
            print(f"Failed to r/w in '{self.my_output_file}'!")
            print(f"{e}")

    def _generate_output_scfile(self):
        try:
            jsonargs = {
                'myjsondata': self.myjsonfile}
            output_scfile_data = self._loadj2(OutputSCJ2, jsonargs)
            os.mknod(self.decrypt_file)
            sopsDecryptcmd = (
                f'sops -d {self.my_output_scfile} > {self.decrypt_file}')
            self._run_shell(sopsDecryptcmd, use_shell=True)
            with open(self.decrypt_file) as drypt_file:
                drypt_data = yaml.safe_load(drypt_file.read())
            for sops_key, sops_val in drypt_data['data'].items():
                drypt_data['data'][sops_key] = base64.b64decode(sops_val).decode('utf8')
                if sops_key in output_scfile_data['data']:
                    drypt_data['data'][sops_key] = output_scfile_data['data'][sops_key]
                drypt_data['data'][sops_key] = (drypt_data['data'][sops_key].encode('ascii'))
                drypt_data['data'][sops_key] = base64.b64encode(drypt_data['data'][sops_key]).decode('utf8')
            with open(self.decrypt_file, 'w') as decrypt_out_file:
                json.dump(drypt_data, decrypt_out_file, indent=4)
        except Exception as e:
            print(f"Failed to create '{self.my_output_scfile}'!")
            print(f"{e}")
        finally:
            try:
                os.remove(self.decrypt_file)
            except Exception:
                print("failed... "
                      f"'{self.decrypt_file}'")

    def newgenerate(self):
        self._generate_output_file()
        self._generate_output_scfile()

def _my_args():
    parser = argparse.ArgumentParser(
        description='Passing input arguments')
    parser.add_argument('-p', '--myjsonfile',
                        required=True,
                        action='store',
                        help='my Json data file')
    args = vars(parser.parse_args())
    print('hello')
    return args

args = _my_args()
MyPythonCode(
    args['myjsonfile']
    ).newgenerate()