// ####################################################################################

// --- RENDERING PAGES --- //
var RenderUrlsToFile, arrayOfUrls, system, fs;
var xpaths = [];
var MAX_WIDTH = 1280;
system = require("system");
fs = require('fs');

/*
Render given urls
@param URL to render
@param output path
*/

RenderUrl = function(url, output_path) {
    var getImagePath, getImageFilename, getAnnotationPath, getListPath, formatNumberLength, next, page, retrieve, urlIndex, webpage;
    
    urlIndex = 0;
    webpage = require("webpage");
    page = null;
    
    saveDomTree = function(dom_tree_path, dom_tree) {    
        var dom_content = JSON.stringify(dom_tree);
        fs.write(dom_tree_path, dom_content, 'w');
    };
    
    getImagePath = function(output_path) {
        return output_path+"/screenshot.jpeg"
    }

    getDOMPath = function(output_path){
        return output_path+"/dom.json"
    }

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

            
    page = webpage.create();
    page.viewportSize = {
        width: MAX_WIDTH,
        height: 800
    };

    page.settings.userAgent = "Mozilla/5.0 (Macintosh; Intel Mac OS X) AppleWebKit/538.1 (KHTML, like Gecko) PhantomJS/2.0.0 Safari/538.1; CVUT-Cloud_Computing_Center BOT (http://3c.felk.cvut.cz/bot/)"
    page.onConsoleMessage = function(msg) {
      console.log(msg);
    };

    page.open(url, function(status) {
        var file;
       
        image_path = getImagePath(output_path);
        dom_tree_path = getDOMPath(output_path);
        console.log(image_path)

        //succeded
        if (status === "success") {
            console.log('success')

            // after 200 ms - press ESCAPE
            window.setTimeout((function() {
                page.sendEvent('keypress', page.event.key.Escape);
                // page.sendEvent('click', 1199, 1, button='left');
            }), 1000);

            // after 2000 ms - start parsing and rendering
            window.setTimeout((function() {
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

                    // save screenshot
                    page.render(image_path,{format: 'jpeg', quality: '100'});
                    
                    // save DOM tree
                    saveDomTree(dom_tree_path, dom_tree)
                    page.close();
                    phantom.exit();
            }), 2000);
            // phantom.exit();
        } 

        // not succeded
        else {
            console.log('not success')
            phantom.exit(1);
        }
    });
};

// ################################################################################
// ################################## MAIN PART ###################################
// ################################################################################

// --- READ PARAMS --- //
if (system.args.length == 3) {
    var url = system.args[1];
    var output_path = system.args[2];
} else {
    console.log("Usage: phantomjs download_page.js URL OUTPUT_PATH");
    phantom.exit(1);
}

// --- RUN --- //
RenderUrl(url, output_path);
