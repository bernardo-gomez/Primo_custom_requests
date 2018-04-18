# Primo_custom_requests
Webservice that supports ARES,ILLIAD,AEON requests.

## Current custom requests:
  1. Document delivery via ILLIAD;
  2. Place on Reserves via ARES;
  3. Book MARBL item via AEON;
  4. Book MARBL item via Finding Aid.
  
## Description:
 This application adds Request Links to Primo Full Record display.
 The display of the Request Links is controlled by a Jquery script that resides 
 in [primo server] fe_web → uploaded_files/discovere/static_htmls/eulFooter.html
 
  Jquery issues a CORS request https://libapiproxyprod1.library.emory.edu/cgi-bin/primo_request?doc_id="+merged_record_id+"&user_id="+bg_user_id to Alma to retrieve the applicable request links for the given user_id and doc_ids.
The response from primo_request webservice is an XML object. Example:

 &lt;result&gt;
 
&lt;code&gt;OK&lt;/code&gt;

&lt;link&gt;

&lt;request_link&gt;

&lt;reserves&gt;

https://libapiproxyprod1.library.emory.edu/cgi-bin/process_reserves_primo_new?doc_id=990011236720302486&user_id=0036487

&lt;/reserves&gt;

&lt;docdelivery&gt;

https://libapiproxyprod1.library.emory.edu/cgi-bin/document_delivery_primo_new?doc_id=990011236720302486&user_id=0036487

&lt;/docdelivery&gt;

&lt;/request_link&gt;

&lt;worldcat_identity&gt; http://worldcat.org/identities/lccn-n91005712/ &lt;/worldcat_identity&gt;

&lt;/link&gt;

&lt;user_group&gt;23&lt;/user_group&gt;

&lt;/result&gt;


Based on the above response, eulFooter.html will display two request links: “reserves” and “docdelivery”.

Webservice **primo_request** resides on the API proxy server ( libapiproxyprod1.library.emory.edu, AKA kleene.library.emory.edu ).




**Primo Request files**:

   **/usr/local/cgi-bin/primo_request** is a CGI wrapper;
   
   **/path_to/webserver/config/primo_request.cfg** ;
   
   **/path_to/webserver/config/alma_request_table.txt** contains applicable requests  based on user_group, holding_library, location, material_type and whether bibliographic record is considered an “archive”.
   External view: https://kleene.library.emory.edu/alma_request_table.html

   **/path_to/webserver/bin/primo_request.py**  builds the list of applicable request links for the items belonging to the bibliographic record, based on alma_request_table.txt. List is packaged in XML object.
  

   **/usr/local/cgi-bin/document_delivery_primo_new** is a CGI wrapper;

   **/usr/local/cgi-bin/process_reserves_primo_new** is a CGI wrapper;

   **/usr/local/cgi-bin/process_booking_primo_new** is a CGI wrapper;

   **/usr/local/cgi-bin/booking_findingaids** is a CGI wrapper.

   **/path_to/webserver/bin/process_primo_request.py** builds the openurl request for one of the three Atlas-sys applications: Ares (reserves), ILLIAD (document_delivery) and Aeon (MARBL booking).


   **/path_to/webserver/bin/booking_finding_aids.py** builds a URL based on the the MARC 555$u  subfield of bibliographic records considered “archive” by the MARC 008 field.


