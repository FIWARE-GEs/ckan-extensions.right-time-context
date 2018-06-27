ckan.module('ngsiview',function(jQuery,_){
    return{
		options:{
	        i18n:{error:_('An error occurred: %(text)s %(error)s')},
			parameters:{contentType:'application/json',
			            dataType:'json',
			            dataConverter:function(data){return JSON.stringify(data,null,2);},
			            language:'json',type:'GET'}
			},
			initialize:function(){
			    var self=this;
			    var p;
			    p=this.options.parameters;
			    if(typeof(view_enable) == 'undefined'){
			        view_enable = [];
                    view_enable[0] = true;
			        resource_url = preload_resource['url']
			    }
			    if(view_enable[0]){
                    jQuery.ajax(resource_url,{type:p.type,contentType:p.contentType,dataType:p.dataType,success:function(data,textStatus,jqXHR){
                        data=p.dataConverter?p.dataConverter(data):data;
                        var highlighted;
                        if(p.language){highlighted=hljs.highlight(p.language,data,true).value;}
                        else{highlighted='<pre>'+data+'</pre>';}
                        self.el.html(highlighted);
                    },
                    error:function(jqXHR,textStatus,errorThrown){
                        if(textStatus=='error'&&jqXHR.responseText.length){self.el.html(jqXHR.responseText);}
                        else{self.el.html(self.i18n('error',{text:textStatus,error:errorThrown}));}}});
                }
                else{
                    self.el.html("\n\n\n"+view_enable[1]+"\n\n\n");
                }

            }};});
