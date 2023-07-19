// ####################################################################################

// --- RENDERING PAGES --- //
var RenderUrlsToFile, arrayOfUrls, system, fs;
var xpaths = [];
var MAX_WIDTH = 1280;
system = require("system");
fs = require('fs');

/*
Render given urls
@param array of URLs to render
@param output path
@param prefix to use
@param callbackPerUrl Function called after finishing each URL, including the last URL
@param callbackFinal Function called after finishing everything
*/

RenderUrlsToFile = function(urls, output_path, prefix, callbackPerUrl, callbackFinal) {
    var getImagePath, getImageFilename, getAnnotationPath, getListPath, formatNumberLength, next, page, retrieve, urlIndex, webpage;
    
    urlIndex = 0;
    webpage = require("webpage");
    page = null;
    
    
    getImagePath = function(output_path, prefix, urlIndex) {
        return output_path+"/images/"+getPageID(prefix, urlIndex)+".jpeg"
    }

    getPageID = function(prefix, urlIndex) {
        return prefix+"-"+formatNumberLength(urlIndex,6)
    }    

    getDOMPath = function(output_path, prefix, urlIndex){
        return output_path+"/dom_trees/"+getPageID(prefix, urlIndex)+".json"
    }

    getHTMLPath = function(output_path, prefix, urlIndex){
        return output_path+"/htmls/"+getPageID(prefix, urlIndex)+".html"
    }

    getListPath = function(output_path, prefix){
        return output_path+'/downloaded_pages/'+prefix+".txt"
    }

    formatNumberLength = function(num, length) {
        var r = "" + num;
        while (r.length < length) {
            r = "0" + r;
        }
        return r;
    }

    // function - closes page, and gets another one
    next = function(status, url, image_filename, annotation_path, list_path, typedObjects, visibleBBs, textBBs) {
        page.close();
        callbackPerUrl(status, url, image_filename, annotation_path, list_path, typedObjects, visibleBBs, textBBs);
        return retrieve();
    };

    // returns DOM tree root with all its descendents
    // each node includes additional useful information - such as position, etc. 
    getDOMTree = function(){
        baseurl = window.location

        var selected_style_props = ['display','visibility','opacity','z-index','background-image','content','image'];

        //-- get elements in processing order
        getElements = function(){
            var tree_stack = new Array();
            var result_stack = new Array();
            tree_stack.push(document);
            // if we have some other nodes
            while (tree_stack.length != 0){
                // get element
                el = tree_stack.pop();
                // put it in result stack
                result_stack.push(el);
                //add children of element to stack
                for (i=0;i<el.childNodes.length;i++){
                    tree_stack.push(el.childNodes[i])
                }
            }
            return result_stack
        }

        //-- creates node with all information
        createNode = function(element){
            node = {};
            node.name = element.nodeName;
            node.type = element.nodeType;

            //VALUE
            if (element.nodeValue){
                node.value =element.nodeValue;
            }
            //COMPUTED STYLE
            computed_style = window.getComputedStyle(element);    
            if (computed_style){
                node.computed_style = {}
                for (i=0;i<selected_style_props.length;i++){
                    style_prop = selected_style_props[i]
                    node.computed_style[style_prop]=computed_style[style_prop]
                }
            }
            //POSITION
            try{
                // IT HAS BOUNDINGCLIENTRECT
                if(typeof element.getBoundingClientRect === 'function') {
                    bb = element.getBoundingClientRect()
                    node.position = [Math.round(bb.left), Math.round(bb.top), Math.round(bb.right), Math.round(bb.bottom)]
                // TRY TO COMPUTE IT
                }else{
                    bb = null
                    var range = document.createRange();
                    range.selectNodeContents(element);
                    bb = range.getBoundingClientRect();
                    if (bb){
                        node.position = [Math.round(bb.left), Math.round(bb.top), Math.round(bb.right), Math.round(bb.bottom)]
                    }
                }
            }catch(err){} 
            // ATRIBTURES
            attrs = element.attributes
            if (attrs){
                node.attrs = {}
                for (i=0;i<attrs.length;i++){
                    node.attrs[attrs[i].nodeName] = attrs[i].nodeValue
                }
            }
            return node
        }

        //---------- RUN -----------//
        element_stack = getElements()
        processed_stack = new Array();

        while (element_stack.length != 0){
            element = element_stack.pop();
            // node
            node = createNode(element)
            // add children
            if (element.childNodes.length>0){
                node.childNodes = []
                for (i=0; i<element.childNodes.length;i++){
                    childNode = processed_stack.pop();
                    node.childNodes.unshift(childNode);
                }
            }
            // add result to stack
            processed_stack.push(node)        
            //console.log(processed_stack.length)
        }
        return processed_stack.pop()
    }

   
    // function - render next url
    retrieve = function() {
        var url;
        if (urls.length > 0) {
            url = urls.shift();
            urlIndex++;
            
            page = webpage.create();
            page.viewportSize = {
                width: MAX_WIDTH,
                height: 800
            };

            page.settings.userAgent = "Mozilla/5.0 (Macintosh; Intel Mac OS X) AppleWebKit/538.1 (KHTML, like Gecko) PhantomJS/2.0.0 Safari/538.1; CVUT-Cloud_Computing_Center BOT (http://3c.felk.cvut.cz/bot/)"
            page.onConsoleMessage = function(msg) {
              console.log(msg);
            };

            return page.open(url, function(status) {
                var file;
               
                image_path = getImagePath(output_path, prefix,urlIndex);
                pageID = getPageID(prefix,urlIndex);
                dom_tree_path = getDOMPath(output_path, prefix,urlIndex);
                html_path = getHTMLPath(output_path, prefix,urlIndex);
                list_path = getListPath(output_path,prefix);
                
                //succeded
                if (status === "success") {
                
                    //after 200 ms - press ESCAPE
                    window.setTimeout((function() {
                        page.sendEvent('keypress', page.event.key.Escape);
                        page.sendEvent('click', 1199, 1, button='left');
                    }), 1000);

                     //after 300 ms - start parsing and rendering
                    return window.setTimeout((function() {
                            var html = page.content
                            var dom_tree = page.evaluate(getDOMTree);

                            // before rendering
                            // add white background in order to override black jpeg default
                            page.evaluate(function() {
                              var style = document.createElement('style'),
                                  text = document.createTextNode('body { background: #ffffff }');
                              style.setAttribute('type', 'text/css');
                              style.appendChild(text);
                              document.head.insertBefore(style, document.head.firstChild);
                            });

                            page.render(image_path,{format: 'jpeg', quality: '100'});
                            return next(status, url, pageID, dom_tree_path, html_path, list_path, dom_tree, html);
                    }), 2000);
                } 
                // not succeded
                else {
                    return next(status, url, pageID, dom_tree_path, html_path, list_path, null, null);
                }
            });
        } else {
            return callbackFinal();
        }
    };

    // remove downloaded file
    listPath = getListPath(output_path, prefix)
    // if exists, remove
    if (fs.exists(listPath)){
        fs.remove(listPath);
    }

    return retrieve();
};

// ####################################################################################

// --- FUNCTIONS --- //

// --- URL PROCESSED - CALLBACK FUNCTION
callbackPerUrl = function(status, url, pageID, dom_tree_path, html_path, listPath, dom_tree, html) {   //, typedObjects, visibleBBs, textBBs
    // Save only succesful renders
    if (status === "success"){
        console.log(url);

        // if does not exist, start array
        if (!fs.exists(listPath)){
            fs.write(listPath, pageID+"\t"+url, 'w+');
        }else{
            fs.write(listPath, "\n"+pageID+"\t"+url, 'w+');
        }

        // write DOM tree
        var dom_content = JSON.stringify(dom_tree);
        fs.write(dom_tree_path, dom_content, 'w');
        // write HTML
        fs.write(html_path,html, 'w');
        return;    
    }
    // Could not parse all xpaths
    else if (status === "parsing_error"){
        return console.error("Parsing error '" + url + "'");
    }
    // Could not download
    else{
        return console.error("Unable to render '" + url + "'");
    }
};

// --- Final CALLBACK FUNCTION 
callbackFinal = function() {
    // close array
    return phantom.exit();
};

// ####################################################################################

// --- READ PARAMS --- //
arrayOfUrls = null;
if (system.args.length == 2) {
    // var input_path = system.args[1];
    // var output_path = system.args[2];
    // var prefix = system.args[3];
    var prefix = system.args[1];
    var input_path = "../data_shops/shop_urls/"+prefix+".txt"
    var output_path = "../data_shops"
} else {
    console.log("Usage: phantomjs download_shop.js PREFIX");
    phantom.exit(1);
}

// --- LOAD URLS ---//
f = fs.open(input_path, "r");
content = f.read();
arrayOfUrls = content.split("\n");

// --- RUN --- //
RenderUrlsToFile(arrayOfUrls, output_path, prefix ,callbackPerUrl, callbackFinal);
