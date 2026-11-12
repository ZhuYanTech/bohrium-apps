## 输入、参数和结果

上传一个文件或粘贴一条分子表达式。多分子请上传文件。默认自动检测，输出 mol。常用格式代码有 smi、can、sdf、mol、mol2、pdb、pdbqt、xyz、cif、inchi、cml。坐标填 none、2d 或 3d。氢原子处理填 none、add、polar、nonpolar、delete 或 delete_nonpolar。pH 留空时禁用。电荷可填 gasteiger。力场可填 MMFF94、MMFF94s、UFF、GAFF 或 Ghemical。最小化步数默认 250，可设 1 至 5,000。转换输出为 converted.<格式>，执行日志为 run.log。输入 CCO 可得到含 3 个重原子的 MOL 文件。

[开源实现](https://github.com/ZhuYanTech/bohrium-apps/tree/main/apps/open-babel) · [上游开源仓库](https://github.com/openbabel/openbabel)
