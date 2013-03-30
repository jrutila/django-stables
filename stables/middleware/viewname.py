class ViewNameMiddleWare(object):
  def process_view(self, request, view_func, view_args, view_kwargs):  
    request.current_view = {
        'name': ".".join((view_func.__module__, view_func.__name__)),
        'args': view_args,
        'kwargs': view_kwargs
        }

def view_name_context_processor(request):  
  return {  
    'view_name': request.view_name,  
    } 
