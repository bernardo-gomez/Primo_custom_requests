// This javascript file should be included in PRIMO's eulFooter.html

// Author: Bernardo Gomez

<script type="text/javascript">
  jQuery(document).ready(function () {
    // Set environment variable for primo banner JSON
    var environment = "production";
    if (typeof(Storage) !== "undefined"){
      // var currentSessionID = jQuery.PRIMO.session.sessionId;
      var isLoggedIn=jQuery.PRIMO.session.user.isLoggedIn(),
          bg_user_id="",
          bg_patron_status="",
          record_id="",
          merged_record_id="",
          material_type="",
          source_id="",
          marbl_count=0,
          lsc_marbl_count=0,
          reserves_url="",
          docdelivery_url="",
          lsc_count=0,
          return_code="",
          return_ucode="",
          other_libr_count=0,
          bg_genre="",
          abstract="",
          ristype="",
          risdate="",
          ou_url="",
          medusa_url="",
          url_user="",
          marbl_link="",
          worldcat_identity="",
          staff_view_bg="",
          full_view_bg="",
          // re_pattern_gatech=/.*GALI_GIT_ALMA.*/,
          // re_pattern_emo=/.*01EMORY_ALMA.*/,
          re_pattern_gatech=new RegExp(".*GALI_GIT_ALMA.*"),
          re_pattern_emo=new RegExp(".*01EMORY_ALMA.*"),
          gatech_item=false,
          emory_item=false,
          url="https://mail.library.emory.edu/cgi-bin/get_alma_bib?doc_id=990029881400302486";
      console.log("loggedin:"+isLoggedIn);
      var record_count=jQuery.PRIMO.records.length;
      console.log("record_count:"+record_count);
      if (isLoggedIn ){
         bg_user_id=jQuery.PRIMO.session.user.id;
         console.log("user_id:"+bg_user_id);
      }
      else{
         bg_user_id="0";
      }
      if (record_count == 1){
        pnx=jQuery.PRIMO.records[0].getPNX();
        console.log("bernardo captured pnx:"+pnx);
        parser=new DOMParser();
        xmlDoc = parser.parseFromString(pnx,"text/xml");
        x = xmlDoc.documentElement.childNodes;
        txt="";

        for (i = 0; i < x.length ;i++) {
           if (x[i].nodeName == "search"){
               search_node=x[i].childNodes;
               for (j=0; j< search_node.length;j++){
                  if (search_node[j].nodeName == "addsrcrecordid"){
                    record_id=search_node[j].childNodes[0].nodeValue;
                    if (merged_record_id == ""){
                        merged_record_id=record_id;
                    }
                    else{
                        merged_record_id=merged_record_id+","+record_id;
                    }

                  }
               }
           }
           if (x[i].nodeName == "control"){
               control_node=x[i].childNodes;
               for (j=0; j< control_node.length;j++){
                  if (control_node[j].nodeName == "sourceid"){
                    source_id=control_node[j].childNodes[0].nodeValue;
                    if (re_pattern_emo.test(source_id)){
                       emory_item=true;
                       console.log("emory item");
                    }
                    if (re_pattern_gatech.test(source_id)){
                       gatech_item=true;
                       console.log("gatech item");
                    }
                    console.log("sourceid:"+source_id);

                  }
               }
           }
           if (x[i].nodeName == "addata"){
               addata_node=x[i].childNodes;
               first_element=true;
               node_value="XXX";
               openurl_text="";
               for (j=0; j< addata_node.length;j++){
                  node_name=addata_node[j].nodeName;
                  if (node_name != "#text"){
                    node_name="rft."+node_name;
                    node_value=addata_node[j].childNodes[0].nodeValue;
                    node_value=encodeURIComponent(node_value);
                    //node_value=node_value.substr(0,80);
                    text_part=node_value.split("%20");
                    short_node_value="";
                    if (text_part.length > 1){
                        for (k=0; k< text_part.length; k++){
                            if (short_node_value == ""){
                               short_node_value=text_part[k];
                            }
                            else{
                               if (short_node_value.length+ text_part[k].length < 80){
                                  short_node_value=short_node_value+"%20"+text_part[k];
                               }
                               else{
                                  break;
                               }
                            }
                        }
                        node_value=short_node_value;
                    }

                    if (node_name == "genre"){
                           if (node_value == "unknown"){
                               node_value="journal";
                           }
                    }
                    if (first_element){
                        openurl_text="&"+node_name+"="+node_value;
                        first_element=false;
                    }
                    else{
                        openurl_text=openurl_text+"&"+node_name+"="+node_value;
                    }
                  }
               }
               base_url="https://reserves.library.emory.edu/shib/ares.dll/openurl?ctx_ver=Z39.88-2004ctx_enc=info:ofi/enc:UTF-8&ctx_enc=info:ofi/enc:UTF-8&=url_ver=Z39.88-2004&url_ctx_fmt=infofi/fmt:kev:mtx:ctx&rft_val_fmt=info:ofi/fmt:kev:mtx:journal&rfr_id=info:sid/primo.exlibrisgroup.com:primo3-Journal-emory_sfx?";
               console.log("openurl:"+base_url+openurl_text);
           }
        }
        console.log("merged_record_id:"+merged_record_id);
        if (emory_item){

             full_view_bg="https://mail.library.emory.edu/cgi-bin/full_view_primo?doc_id="+merged_record_id;
             $('.EXLDetailsLinks ul').append('<li><span class="EXLDetailsLinksBullet"></span><a href="'+full_view_bg+'" target="_blank" id="full_view_bg" title="See all the information for this tile">Full View</a></li>');
             report_alma_error="https://mail.library.emory.edu/cgi-bin/report_alma_error?doc_id="+merged_record_id;
//             $('.EXLDetailsLinks ul').append('<li><span class="EXLDetailsLinksBullet"></span><a href="'+report_alma_error+'" target="_blank" id="full_view_bg" title="Report an error about this record">Report an error</a></li>');
             staff_view_bg="https://mail.library.emory.edu/cgi-bin/get_alma_bib?doc_id="+merged_record_id+"&format=marcedit";
             sendtophone_bg="https://mail.library.emory.edu/cgi-bin/sendtophone?doc_id="+merged_record_id;
             qrcode_bg="https://mail.library.emory.edu/cgi-bin/qrcode?doc_id="+merged_record_id;
             html_sendtophone='<li class="EXLButtonSendToPhone"><a href="'+sendtophone_bg+'" title="Send item information to your smart device" target="_blank" id="sendtophone_bg"><span class="EXLButtonSendToLabel">Send To Phone</span><span class="EXLButtonSendToIcon EXLButtonSendToIconPhone"></span></a></li>';
             html_qrcode='<li class="EXLButtonSendToQRCode"><a href="'+qrcode_bg+'" title="Scan QR Code"" target="_blank" id="qrcode_bg"><span class="EXLButtonSendToLabel">QR Code</span><span class="EXLButtonSendToIcon EXLButtonSendToIconQRCode"></span></a></li>';
             $('ol.EXLTabHeaderButtonSendToList').append(html_sendtophone);
             $('ol.EXLTabHeaderButtonSendToList').append(html_qrcode);
             $('.EXLDetailsLinks ul').append('<li><span class="EXLDetailsLinksBullet"></span><a href="'+staff_view_bg+'" target="_blank" id="staff_view_bg" title="Raw MARC data in MARCEdit format">Staff View</a></li>');

        }
        if (emory_item ){
             medusa_url="https://libapiproxyprod1.library.emory.edu/cgi-bin/primo_request?doc_id="+merged_record_id+"&user_id="+bg_user_id;
            console.log("medusa_url:"+medusa_url);
            jQuery.ajaxSetup({async:false});
            jQuery.get(medusa_url,function(xdata){
              parser=new DOMParser();
              xml_doc = parser.parseFromString(xdata,"text/xml");
              xnode=xml_doc.documentElement.childNodes;
              for (k = 0; k < xnode.length ;k++) {
                if (xnode[k].nodeName == "user_group"){
                    bg_patron_status=xnode[k].childNodes[0].nodeValue;
                    console.log("user_group:"+bg_patron_status);
                }
                if (xnode[k].nodeName == "link"){
                    links=xnode[k].childNodes;
                    for (j=0; j< links.length; j++){
                        if (links[j].nodeName == "request_link"){
                           reqnode=links[j].childNodes;
                           console.log("request links here "+reqnode.length);
                           if (reqnode.length > 0){
                             console.log("request links here ");
                             for (rr = 0; rr< reqnode.length; rr++){
                               console.log("reqlink:"+reqnode[rr].nodeName);
                               if (reqnode[rr].nodeName == "reserves"){
                                  reserves_url=reqnode[rr].childNodes[0].nodeValue;
                               }
                               if (reqnode[rr].nodeName == "docdelivery"){
                                  docdelivery_url=reqnode[rr].childNodes[0].nodeValue;
                               }
                               if (reqnode[rr].nodeName == "marbl_booking"){
                                  marbl_link=reqnode[rr].childNodes[0].nodeValue;
                               }
                               if (reqnode[rr].nodeName == "marbl_finding_aids"){
                                  marbl_link=reqnode[rr].childNodes[0].nodeValue;
                               }
                             }
                           }
                        }
                        else if (links[j].nodeName == "worldcat_identity"){
                             try{
                                worldcat_identity=links[j].childNodes[0].nodeValue;
                             }
                             catch(err){
                                worldcat_identity="";
                             }
                        }
                    }
                }
              }
           },"text");
        }
            // return_code="OK";   // TEST
            //  if (return_code == "OK"){
             if (worldcat_identity != ""){
//                $('.EXLDetailsLinks ul').append('<li><span class="EXLDetailsLinksBullet"></span><a href="'+worldcat_identity+'" target="_blank" id="staff_view_bg" title="Information about this author">More information about this author</a></li>');
             }
                    if (marbl_link != ""){
                       this_url="<a href="+marbl_link+" target=\"_blank\" id=\"reserves_bg\" title=\"Request from Rose  Library\">Request from Rose Library</a>";
                       console.log("will produce marbl link:"+this_url);
                       $('#exlidResult0-TabsList').append('<li id="EULAresLink" class="EXLResultTab">'+this_url+'</li>');
                    }
                    if (reserves_url != ""){
                       this_url="<a href="+reserves_url+" target=\"_blank\" id=\"reserves_bg\" title=\"Place this item on Reserves\">Place on Reserves</a>";
                       console.log("will produce ares link:"+this_url);
                       $('#exlidResult0-TabsList').append('<li id="EULAresLink" class="EXLResultTab">'+this_url+'</li>');
                    }
                    if (docdelivery_url != ""){
                       this_url="<a href="+docdelivery_url+" target=\"_blank\" id=\"docdevlivery_bg\" title=\"Request delivery\">Document Delivery</a>";
                       console.log("will produce illiad link:"+this_url);
                       $('#exlidResult0-TabsList').append('<li id="EULIlliadLink" class="EXLResultTab">'+this_url+'</li>');
                    }
             //  }


//        bg_patron_status="01";
        console.log("here3:"+source_id+ ":"+bg_patron_status);


     }
      if (! gatech_item && ! emory_item ){
            console.log("PCI item here");
         console.log("user_id:"+bg_user_id);
         url_user="https://mail.library.emory.edu/cgi-bin/get_alma_patron_status?user_id="+bg_user_id;
         jQuery.ajaxSetup({async:false});
         jQuery.get(url_user,function(udata){
            parseru=new DOMParser();
            xml_udoc = parseru.parseFromString(udata,"text/xml");
            xnodeu=xml_udoc.documentElement.childNodes;
            for (uk = 0; uk < xnodeu.length ;uk++) {
              if (xnodeu[uk].nodeName == "code"){
                  return_ucode=xnodeu[uk].childNodes[0].nodeValue;
                  console.log("return_code patron status:"+return_ucode);
              }
              if (xnodeu[uk].nodeName == "patron_status"){
                  bg_patron_status=xnodeu[uk].childNodes[0].nodeValue;
                  console.log("patron_status:"+bg_patron_status);
              }
            }
         },"text");



         if (bg_patron_status == "01" || bg_patron_status == "10" ||  bg_patron_status == "23"){
           console.log("openurl for ares here");
           this_url="<a href="+base_url+openurl_text+" target=\"_blank\" id=\"reserves_bg\" title=\"Place this item on Reserves\">Place on Reserves</a>";
           console.log("will produce ares link:"+this_url);
           $('#exlidResult0-TabsList').append('<li id="EULAresLink" class="EXLResultTab">'+this_url+'</li>');
         }

      }
   }
    });
</script>

