### Progress Bar widget 
### Original work https://github.com/tqdm/tqdm


# Usage

#### in HTML
```html
<div> {{{sly_tqdm.to_html(identifier = 'unique_identifier') | safe }}} </div>
```


#### in Python
```python
from supervisely.app.widgets import sly_tqdm

for _ in sly_tqdm(range(10), identifier='unique_identifier', message='Iterations'):
    pass
```