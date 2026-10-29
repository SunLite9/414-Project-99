"""Convert a '# %%'-delimited script into a Jupyter notebook ('# %% [markdown]' cells hold markdown as # comments)."""
import sys, nbformat as nbf
src=open(sys.argv[1]).read(); nb=nbf.v4.new_notebook(); cells=[]
for block in src.split('# %%')[1:]:
    head,_,body=block.partition('\n')
    if head.strip().startswith('[markdown]'):
        cells.append(nbf.v4.new_markdown_cell('\n'.join(l[2:] if l.startswith('# ') else l.lstrip('#') for l in body.strip().splitlines())))
    else: cells.append(nbf.v4.new_code_cell(body.strip()))
nb.cells=cells; nb.metadata['kernelspec']={'name':'python3','display_name':'Python 3','language':'python'}
nbf.write(nb,sys.argv[2])
