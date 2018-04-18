#!/bin/env python
# -*- coding: utf-8 -*-

r"""
   'table' class processes alma_request_table file.
  
"""
__author__ = "bernardo gomez"
__date__ = " march 2017"
import os
import sys
import re
class table:
  def __init__(self,request_map):
    """
      it receives a text file with request entries.
      columns in an entry:
      user_group|library|location|material_type|archive|request_type@form_type
      a bibliographic record is deemed "archive" (Y/N) if position 6
      in the leader is "p". 
      form_type normally refers to atlas-sys genre ("book","conference", etc)

      init function stores table as a list of strings.
    """
    try:
       req_file=open(request_map,'Ur')
    except:
       sys.stderr.write("couldn't open "+request_map+"|\n")
       raise Exception
    self.req_table=[]
    for line in req_file:
      line=line.rstrip("\n")
      try:
          field=line.split("|")
      except:
         sys.stderr.write("defective request table:"+line+"\n")
         raise Exception

      self.req_table.append(field)
    if len(self.req_table[0]) != 6:
        req_file.close()
        sys.stderr.write("split failed\n")
        raise Exception
    req_file.close()
    return

  def get_menu(self,context):

       """
         get_menu receives a request context 
         (user_group|library|location|material_type|archive|)
         and returns the applicable requests (type@form) as
         a list of strings.
       """
       url=""
       if len(self.req_table[0]) != 6:
          return url
       column=context.split("|")
       match=False
       for row in self.req_table:
           user_group=str(row[0]).split(",")
           library=str(row[1]).split(",")
           location=str(row[2]).split(",")
           material_type=str(row[3]).split(",")
           archive=str(row[4]).split(",")
           if str(row[0])  == "#":
              match=True
           elif str(column[0]) in user_group:
              match=True
           else:
              match=False
           if match:
              if str(row[1])  == "#":
                 match=True
              elif str(column[1]) in library:
                 match=True
              else:
                 match=False
              if match:
                 if str(row[2])  == "#":
                    match=True
                 elif str(column[2]) in location:
                    match=True
                 else:
                    match=False
                 if match: 
                    if str(row[3])  == "#":
                       match=True
                    elif str(column[3]) in material_type:
                        match=True
                    else:
                        match=False
                    if match:
                       if str(row[4])  == "#":
                          match=True
                       elif str(column[4]) in archive:
                           match=True
                       else:
                           match=False
                       if match:
                          url=str(row[5])
                          break
       #sys.stderr.write("req_type:"+url+"\n")
       return str(url)

  def match_it(self,context):
       """
         match_it receives a request context 
         (user_group|library|location|material_type|archive|)
         and it asserts (True/False)  whether the context is in the 
         request table.
       """
       match=False
       if len(self.req_table[0]) != 6:
          return match
       column=context.split("|")
       match=False
       for row in self.req_table:
           user_group=str(row[0]).split(",")
           library=str(row[1]).split(",")
           location=str(row[2]).split(",")
           material_type=str(row[3]).split(",")
           archive=str(row[4]).split(",")
           if str(row[0])  == "#":
              match=True
           elif str(column[0]) in user_group:
              match=True
           else:
              match=False
           if match:
              if str(row[1])  == "#":
                 match=True
              elif str(column[1]) in library:
                 match=True
              else:
                 match=False
              if match:
                 if str(row[2])  == "#":
                    match=True
                 elif str(column[2]) in location:
                    match=True
                 else:
                    match=False
                 if match: 
                    if str(row[3])  == "#":
                       match=True
                    elif str(column[3]) in material_type:
                        match=True
                    else:
                       match=False
                    if match:
                        if str(row[4])  == "#":
                           match=True
                        elif str(column[4]) in archive:
                           match=True
                        else:
                           match=False
                        if match:
                          break

       return match 
