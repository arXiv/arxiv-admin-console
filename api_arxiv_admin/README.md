# Biz logic mapping

    site-src/lib/arXiv/endorsement-policy.php.m4:      $auth->conn->query_raw("INSERT INTO arXiv_endorsements (endorser_id,endorsee_id,archive,subject_class,flag_valid,type,point_value,issued_when,request_id) VALUES ($_endorser,'$_endorsee','$_archive','$_subject_class',1,'$_type',$point_value,$auth->timestamp,$_request_id)");
    site-src/lib/arXiv/endorsement-policy.php.m4:      $auth->conn->query("INSERT INTO arXiv_endorsements_audit (endorsement_id,session_id,remote_addr,remote_host,tracking_cookie,flag_knows_personally,flag_seen_paper,comment) VALUES (LAST_INSERT_ID(),$auth->session_id,'$_remote_addr','$_remote_host','$_tracking_cookie',$_flag_knows_personally,$_flag_seen_paper,'$_comment')");
    site-src/lib/arXiv/endorsement-policy.php.m4:        $auth->conn->query("UPDATE arXiv_demographics SET flag_suspect=1 WHERE user_id='$_endorsee'");
    site-src/lib/arXiv/endorsement-policy.php.m4:        $auth->conn->query("UPDATE arXiv_demographics SET flag_suspect=1 WHERE user_id='$_endorsee'");
    site-src/lib/arXiv/endorsement-policy.php.m4:        $auth->conn->query("UPDATE arXiv_endorsement_requests SET point_value=point_value+$point_value WHERE request_id=$_request_id");


## Show paper password

    site-src/code=/recover-paper-pw-head.php.m4:  $r=$auth->conn->query("SELECT document_id FROM arXiv_documents WHERE paper_id='$_paper_id'");
    site-src/code=/recover-paper-pw-head.php.m4:  $r=$auth->conn->query("SELECT COUNT(*) FROM arXiv_paper_owners WHERE document_id=$document_id AND user_id=$auth->user_id");
    site-src/code=/recover-paper-pw-head.php.m4:  $r=$auth->conn->query("SELECT password_storage,password_enc FROM arXiv_paper_pw WHERE document_id=$document_id");

## Create a arXiv_paper_owners record and assign a paper password

    site-src/code=/need-paper-password-action-head.php.m4:  $r=$auth->conn->query($sql);
    site-src/code=/need-paper-password-action-head.php.m4:  $r=$auth->conn->query_raw("INSERT INTO arXiv_paper_owners (user_id,document_id,date,added_by,remote_addr,remote_host,tracking_cookie,valid,flag_author,flag_auto) SELECT $_user_id,document_id,$_date,$_added_by,'$_remote_addr','$_remote_host','$_tracking_cookie',1,$author,0 FROM arXiv_documents WHERE paper_id='$_paper_id'");

## Re-do the document category

    site-src/lib/arXiv/paper.php.m4:      $auth->conn->query("DELETE FROM arXiv_in_category WHERE document_id=$document_id");

       protected function _store_categories() {
          global $auth;
          $document_id=$this->get_document_id();
          $auth->conn->query("DELETE FROM arXiv_in_category WHERE document_id=$document_id");
          $categories=explode(" ",$this->get_field("Categories"));
          $divided=array();
          foreach($categories as $cat) {
             list ($archive,$subject_class)=explode(".",$cat);
             if(!$subject_class) {
                $subject_class="";
             } else {
                $divided[$archive]=true;
             };
             
             $this->_insert_category($archive,$subject_class);
          }
    
          foreach(array_keys($divided) as $archive) {
             $this->_insert_category($archive,"");
          }
       }

## Change author status

    site-src/code=/change-author-status-head.php.m4:      $auth->conn->query("UPDATE arXiv_paper_owners SET flag_author=1 WHERE user_id={$auth->user_id} AND document_id IN ($author_list)");
    site-src/code=/change-author-status-head.php.m4:      $auth->conn->query("UPDATE arXiv_paper_owners SET flag_author=0 WHERE user_id={$auth->user_id} AND document_id IN ($not_author_list)");

## Ownership request

    site-src/code=/request-ownership-head.php.m4:   $auth->conn->query($sql);
    site-src/code=/request-ownership-head.php.m4:   $auth->conn->query($sql);
    site-src/code=/request-ownership-head.php.m4:      $auth->conn->query($sql);


    site-src/code=/index-head-site.php.m4:$r=$auth->conn->query($sql);

    site-src/code=/need-paper-password-head.php.m4:  $r=$auth->conn->query("SELECT nickname FROM tapir_nicknames WHERE user_id=$_user_id AND flag_primary=1");
    site-src/code=/need-paper-password-head.php.m4:    $r=$auth->conn->query($sql);
    site-src/code=/need-paper-password-head.php.m4:    $r=$auth->conn->query_raw($sql);
    site-src/code=/need-paper-password-head.php.m4:       $r=$auth->conn->query("SELECT title FROM arXiv_documents WHERE paper_id='$_paper_id'");

# Endorsement request

    site-src/code=/need-endorsement-head.php.m4:$r=$auth->conn->query("SELECT nickname FROM tapir_nicknames WHERE user_id=$_user_id AND flag_primary=1");
    site-src/code=/need-endorsement-head.php.m4:   $auth->conn->query_raw("INSERT INTO arXiv_endorsement_requests (endorsee_id,archive,subject_class,secret,flag_valid,issued_when) VALUES ($_user_id,'$_archive','$_subject_class','$secret',1,$_issued_when)");
    site-src/code=/need-endorsement-head.php.m4:   } else $auth->conn->query("INSERT INTO arXiv_endorsement_requests_audit (request_id,remote_addr,remote_host,tracking_cookie,session_id) VALUES (LAST_INSERT_ID(),'$_remote_addr','$_remote_host','$_tracking_cookie',$_session_id)");

    site-src/admin/arXiv/reject-cross.m4:$auth->conn->query("

    site-src/admin/code/change-paper-pw-head.php.m4:   $auth->conn->query($sql);

    site-src/admin/arXiv/alter-hold.m4:$auth->conn->query("
    site-src/admin/arXiv/create-hold.m4:         $auth->conn->query("
    site-src/admin/arXiv/create-hold.m4:            $auth->conn->query("
    src/code/index-head.php.m4:	$r=$auth->conn->query("SELECT flag_wants_email,flag_html_email FROM tapir_users WHERE user_id=".$auth->user_id);
    site-src/admin/arXiv/add-new-category.m4:$auth->conn->query("
    src/code/inject-post-variables-head.php.m4:	$rs=$auth->conn->query($q);
    site-src/admin/arXiv/make-primary.m4:$auth->conn->query("
    site-src/admin/code/revoke-paper-owner.php.m4:   $auth->conn->query("UPDATE INTO arXiv_paper_owners SET valid=0 WHERE document_id=$document_id AND user_id=$user_id");
    src/code/update-head.php.m4:    $auth->conn->query("UPDATE tapir_permanent_tokens SET valid=0 WHERE user_id='$_user_id' AND secret='$_secret'");
    src/code/update-head.php.m4:  $r=$auth->conn->query("SELECT password_storage AS old_storage,password_enc FROM tapir_users_password WHERE user_id=$auth->user_id");
    src/code/update-head.php.m4:  $auth->conn->query("UPDATE tapir_permanent_tokens SET valid=0 WHERE user_id='$_user_id'");
    src/code/update-head.php.m4:    $result=$auth->conn->query("SELECT * FROM tapir_users WHERE email='".addslashes($email)."';");
    src/code/update-head.php.m4:    $result=$auth->conn->query("SELECT user_id FROM tapir_nicknames WHERE nickname='".addslashes($nickname)."';");
    src/code/update-head.php.m4:      $result=$auth->conn->query("SELECT * FROM tapir_users WHERE user_id=$user_id;");
    src/code/update-head.php.m4:  $result=$auth->conn->query("SELECT * FROM tapir_users_password WHERE user_id=$user_id");
    src/code/update-head.php.m4:   $result=$auth->conn->query("SELECT email,user_id,recovery_policy FROM tapir_users LEFT JOIN tapir_policy_classes ON tapir_users.policy_class=tapir_policy_classes.class_id WHERE email='$_identifier'");
    src/code/update-head.php.m4:      $result=$auth->conn->query("SELECT email,tapir_users.user_id,recovery_policy FROM tapir_users LEFT JOIN tapir_policy_classes ON tapir_users.policy_class=tapir_policy_classes.class_id LEFT JOIN tapir_nicknames ON tapir_users.user_id=tapir_nicknames.user_id WHERE nickname='$_identifier'");
    src/code/update-head.php.m4:  $result=$auth->conn->query("SELECT nickname FROM tapir_nicknames WHERE flag_primary=1 AND user_id=".$u->user_id);
    src/code/update-head.php.m4:      $auth->conn->query("INSERT INTO tapir_recovery_tokens (user_id,secret,issued_when,issued_to,tracking_cookie,tapir_dest,remote_host) VALUES ('$u->user_id','$secret',$auth->timestamp,'$REMOTE_ADDR','$_cookie','$_tapir_dest','$_remote_host');");
    src/code/update-head.php.m4:   $auth->conn->query("UPDATE tapir_recovery_tokens SET valid=0 WHERE user_id='$user_id' AND secret='$secret'");
    src/code/update-head.php.m4:   $auth->conn->query("INSERT INTO tapir_recovery_tokens_used (user_id,secret,used_when,used_from,session_id,remote_host) VALUES ('$user_id','$secret',$auth->timestamp,'$REMOTE_ADDR','$auth->session_id','$_remote_host');");
    src/code/update-head.php.m4:		$auth->conn->query("INSERT INTO tapir_address (user_id,address_type,company,line1,line2,city,state,postal_code,country) VALUES ($user_id,0,'$_company','$_line1','$_line2','$_city','$_state','$_postal_code','$_country')");
    src/code/update-head.php.m4:		$auth->conn->query("UPDATE tapir_users SET flag_wants_email=$value WHERE user_id=$user_id");
    src/code/update-head.php.m4:    $result=$auth->conn->query("SELECT COUNT(*) FROM tapir_permanent_tokens WHERE user_id='$_user_id' AND secret='$_secret' AND valid=1");
    src/code/update-head.php.m4:      $auth->conn->query("INSERT INTO tapir_permanent_tokens_used (user_id,secret,used_when,used_from,session_id,remote_host) VALUES ('$_user_id','$_secret',$auth->timestamp,'$_remote_addr',$auth->session_id,'$_remote_host') ");
    site-src/admin/code/make-moderator-head.php.m4:      $auth->conn->query($sql);
    site-src/admin/code/make-moderator-head.php.m4:      $auth->conn->query("INSERT INTO arXiv_moderators (user_id,archive,subject_class) VALUES($user_id,'$_archive','$_subject_class')");
    src/lib/tapir-audit.php.m4:	$auth->conn->query("INSERT INTO tapir_admin_audit (log_date,session_id,ip_addr,admin_user,affected_user,tracking_cookie,action,data,comment,remote_host) VALUES ($auth->timestamp,$_session_id,'$_ip_addr',$_admin_user,'$_affected_user','$_tracking_cookie','$_action','$_data','$_comment','$_remote_host')");
    src/code/v-head.php.m4:	$result=$auth->conn->query($sql);
    src/code/v-head.php.m4:	$auth->conn->query("UPDATE tapir_users SET flag_email_verified=1 WHERE user_id='$user_id'");
    src/code/v-head.php.m4:	$auth->conn->query("INSERT INTO tapir_email_tokens_used (user_id,secret,used_when,used_from,session_id,remote_host) VALUES ($user_id,'$_secret',$auth->timestamp,'$_remote_addr',$auth->session_id,'$_remote_host');");
    src/code/v-head.php.m4:	$result=$auth->conn->query("SELECT email FROM tapir_users WHERE user_id=$user_id");
    src/code/no-cookie-head.php.m4:$auth->conn->query("INSERT INTO tapir_no_cookies (log_date,ip_addr,tracking_cookie,session_data,user_agent) VALUES ($auth->timestamp,'$_ip_addr','$_tracking_cookie','$_session_data','$_user_agent')");
    src/code/c-head.php.m4:$result=$auth->conn->query($sql);
    src/code/c-head.php.m4:   $auth->conn->query_raw("UPDATE tapir_users SET email='$_new_email' WHERE user_id=$r->user_id");   
    src/code/c-head.php.m4:   $auth->conn->query("UPDATE arXiv_submissions SET submitter_email='$_new_email' WHERE submitter_email='$old_email' and status = '0'");
    src/code/c-head.php.m4:   $auth->conn->query("INSERT INTO tapir_email_change_tokens_used (user_id,secret,used_when,used_from,session_id,remote_host) VALUES ($r->user_id,'$_secret',$auth->timestamp,'$_remote_addr',$auth->session_id,'$_remote_host');");
    src/code/c-head.php.m4:   $auth->conn->query("UPDATE tapir_email_change_tokens SET used=1 WHERE secret='$_secret'");
    src/code/process-bounce-head.php.m4:$rs=$auth->conn->query("SELECT reference_type,reference_id,email FROM tapir_email_log WHERE mail_id='$_mail_id'");
    src/code/process-bounce-head.php.m4:$auth->conn->query("UPDATE tapir_email_log SET flag_bounced=1 WHERE mail_id='$_mail_id'");
    src/lib/tapir-query.php.m4:		$auth->conn->query($q);
    src/lib/tapir-query.php.m4:			$r=$auth->conn->query($sql);
    site-src/admin/arXiv/unreject-cross.m4:$auth->conn->query("
    site-src/admin/code/change-veto-status-head.php.m4:  $auth->conn->query($sql);
    site-src/admin/code/non-academic-email-head.php.m4:$auth->conn->query("create temporary table black_users select user_id,email,pattern as black_pattern,joined_date,first_name,last_name,suffix_name from tapir_users,arXiv_black_email where joined_date>UNIX_TIMESTAMP(DATE_SUB(CURDATE(),INTERVAL 3 MONTH)) and email like pattern");
    site-src/admin/code/make-moderator-head.php:   $auth->conn->query("INSERT INTO arXiv_moderators (user_id,archive,subject_class) VALUES($user_id,'$_archive','$_subject_class')");
    site-src/admin/code/toggle-author-head.php.m4:   $auth->conn->query("UPDATE arXiv_paper_owners set flag_author=NOT(flag_author),flag_auto=0 WHERE user_id='$_user_id' and document_id='$_document_id'");
    site-src/admin/code/process-ownership-head.php.m4:      $auth->conn->query("UPDATE arXiv_ownership_requests SET workflow_status='rejected' WHERE request_id=$request->request_id");
    site-src/admin/code/process-ownership-head.php.m4:      $auth->conn->query("UPDATE arXiv_ownership_requests SET workflow_status='pending' WHERE request_id=$request->request_id");
    site-src/admin/code/process-ownership-head.php.m4:         $auth->conn->query("UPDATE arXiv_ownership_requests SET workflow_status='accepted' WHERE request_id=$request->request_id");
    site-src/admin/code/process-ownership-head.php.m4:              $auth->conn->query("INSERT INTO arXiv_paper_owners (document_id,user_id,date,added_by,remote_addr,remote_host,tracking_cookie,valid,flag_author,flag_auto) VALUES ($_document_id,$user_id,$auth->timestamp,$auth->user_id,'$_remote_addr','$_remote_host','$_tracking_cookie',1,$flag_author,0)");     
    site-src/admin/code/process-ownership-head.php.m4:         $auth->conn->query("UPDATE arXiv_ownership_requests SET workflow_status='accepted' WHERE request_id=$request->request_id");
    site-src/admin/code/user-category-op-head.php.m4:         $auth->conn->query($sql);
    site-src/admin/code/user-category-op-head.php.m4:         $auth->conn->query("INSERT INTO arXiv_moderators (user_id,archive,subject_class) VALUES($user_id,'$_archive','$_subject_class')");
    site-src/admin/code/user-detail-head-site.php.m4:$r=$auth->conn->query($sql);
    site-src/admin/code/user-detail-head-site.php.m4:$r=$auth->conn->query($sql);
    site-src/admin/code/user-detail-head-site.php.m4:$r=$auth->conn->query($sql);
    site-src/admin/code/user-detail-head-site.php.m4:$r=$auth->conn->query($sql);
    site-src/admin/code/revoke-paper-owner-head.php.m4:   $auth->conn->query("UPDATE arXiv_paper_owners SET valid=$valid WHERE document_id=$document_id AND user_id=$user_id");
    site-src/admin/code/add-paper-owner-head.php.m4:   $auth->conn->query("INSERT INTO arXiv_paper_owners (document_id,user_id,date,added_by,remote_addr,remote_host,tracking_cookie,valid,flag_author,flag_auto) VALUES('$_document_id','$_user_id','$_date','$_added_by','$_remote_addr','$_remote_host','$_tracking_cookie',1,$_flag_author,0)");
    src/lib/tapir-mail.php.m4:		$rs=$auth->conn->query("SELECT template_id,short_name,long_name,data,sql_statement,workflow_status FROM tapir_email_templates WHERE $match='$_identifier'");
    src/lib/tapir-mail.php.m4:		$rs=$auth->conn->query("SELECT header_name,header_content FROM tapir_email_headers WHERE template_id=$template_id");
    src/lib/tapir-mail.php.m4:		$auth->conn->query("INSERT INTO tapir_email_log (reference_type,reference_id,sent_date,email,flag_bounced,mailing_id,template_id) VALUES ('$_reference_type','$_reference_id',$auth->timestamp,'$_to',0,'$_mailing_id',$this->template_id)");
    src/lib/tapir-mail.php.m4:		   $rs=$auth->conn->query("SELECT email,first_name,last_name FROM tapir_users WHERE user_id='$_user_id'");
    src/admin/code/email-template-menu-head.php.m4:$rs=$auth->conn->query("SELECT template_id,CONCAT(short_name,': ',long_name) FROM tapir_email_templates"); 
    src/admin/code/periodic-tasks-head.php.m4:	$auth->conn->query("INSERT INTO tapir_periodic_tasks_log (t,entry) VALUES ($auth->timestamp,'$_log')");
    src/admin/code/email-to-select-head.php.m4:$auth->conn->query("UPDATE tapir_email_templates SET workflow_status=3 WHERE template_id='$_template_id'");
    src/admin/code/edit-form-head.php.m4:$r=$auth->conn->query("SELECT email FROM tapir_users WHERE user_id=$tapir_id");
    src/admin/code/change-password-head.php.m4:$r=$auth->conn->query("SELECT email FROM tapir_users WHERE user_id=$tapir_id");
    src/admin/code/email-template-action-head.php.m4:	$rs=$auth->conn->query("SELECT long_name,data FROM tapir_email_templates WHERE template_id=$_template_id");
    src/admin/code/email-template-action-head.php.m4:	$rs=$auth->conn->query("SELECT header_name,header_content FROM tapir_email_headers WHERE template_id=$_template_id");
    src/admin/code/email-template-action-head.php.m4:	$auth->conn->query("INSERT INTO tapir_email_templates (short_name,long_name,data,update_date,created_by,updated_by,workflow_status) VALUES ('$_short_name','$_long_name','$_data',$auth->timestamp,$_created_by,$_created_by,2)");
    src/admin/code/email-template-action-head.php.m4:		$auth->conn->query("INSERT INTO tapir_email_headers (template_id,header_name,header_content) VALUES ($template_id,'$_key','$_value')");
    src/admin/code/email-template-action-head.php.m4:	$auth->conn->query("UPDATE tapir_email_templates SET short_name='$_short_name' WHERE template_id=$_template_id");
    src/admin/code/email-template-action-head.php.m4:		$auth->conn->query("DELETE FROM tapir_email_headers WHERE template_id=$_template_id");
    src/admin/code/email-template-action-head.php.m4:		$auth->conn->query("DELETE FROM tapir_email_templates WHERE template_id=$_template_id");
    src/admin/code/email-template-action-head.php.m4:	$auth->conn->query("INSERT INTO tapir_email_templates (short_name,long_name,data,update_date,created_by,updated_by,workflow_status) VALUES ('$_short_name','$_long_name','$_data',$auth->timestamp,'$_updated_by','$_updated_by',2)");
    src/admin/code/email-template-action-head.php.m4:	$auth->conn->query("UPDATE tapir_email_templates SET long_name='$_long_name',data='$_data',update_date=$auth->timestamp,updated_by=$_updated_by,workflow_status=2 WHERE template_id=$template_id");
    src/admin/code/email-template-action-head.php.m4:	$auth->conn->query("REPLACE INTO tapir_email_headers (template_id,header_name,header_content) VALUES ('$_template_id','$_header_name','$_header_content')");
    src/admin/code/index-head.php.m4:$rs=$auth->conn->query("SELECT value FROM tapir_integer_variables WHERE variable_id='last_periodic_tasks'");
    src/admin/code/email-template-form-head.php.m4:	$rs=$auth->conn->query("SELECT short_name,long_name,data FROM tapir_email_templates WHERE template_id='$_template_id'");
    src/admin/code/email-template-form-head.php.m4:	$rs=$auth->conn->query("SELECT header_name,header_content FROM tapir_email_headers WHERE template_id='$_template_id'");
    src/admin/code/monitor-box-head.php.m4:$rs=$auth->conn->query("SELECT COUNT(*) FROM tapir_users");
    src/admin/code/monitor-box-head.php.m4:$rs=$auth->conn->query("SELECT COUNT(*) FROM tapir_users WHERE joined_date>$auth->timestamp-24*3600");
    src/admin/code/monitor-box-head.php.m4:$rs=$auth->conn->query("SELECT COUNT(*) FROM tapir_users WHERE joined_date>$auth->timestamp-7*24*3600");
    src/admin/code/monitor-box-head.php.m4:$rs=$auth->conn->query("SELECT COUNT(*) FROM tapir_sessions");
    src/admin/code/monitor-box-head.php.m4:$rs=$auth->conn->query("SELECT COUNT(*) FROM tapir_sessions WHERE start_time>$auth->timestamp-24*3600");
    src/admin/code/monitor-box-head.php.m4:$rs=$auth->conn->query("SELECT COUNT(*) FROM tapir_sessions WHERE start_time>$auth->timestamp-7*24*3600");
    src/admin/code/monitor-box-head.php.m4:$rs=$auth->conn->query("SELECT COUNT(*) FROM tapir_sessions WHERE end_time=0");
    src/admin/code/monitor-box-head.php.m4:$rs=$auth->conn->query("SELECT COUNT(*) FROM tapir_permanent_tokens_used");
    src/admin/code/monitor-box-head.php.m4:$rs=$auth->conn->query("SELECT COUNT(*) FROM tapir_permanent_tokens_used WHERE used_when>$auth->timestamp-24*3600");
    src/admin/code/monitor-box-head.php.m4:$rs=$auth->conn->query("SELECT COUNT(*) FROM tapir_permanent_tokens_used WHERE used_when>$auth->timestamp-7*24*3600");
    src/admin/code/email-to-select-form-head.php.m4:$rs=$auth->conn->query("SELECT template_id,CONCAT(short_name,': ',long_name) FROM tapir_email_templates WHERE workflow_status=2"); 
    src/admin/code/update-head.php.m4:   $auth->conn->query("UPDATE tapir_users SET flag_email_verified=1 WHERE user_id=$user_id");
    src/admin/code/update-head.php.m4:	$auth->conn->query("UPDATE tapir_permanent_tokens SET valid=0 WHERE user_id='$_user_id'");
    src/admin/code/update-head.php.m4:     $auth->conn->query("UPDATE $table SET $column='$code_value' WHERE $key_column=$tapir_id");
    src/admin/code/update-head.php.m4:     $auth->conn->query("UPDATE $table SET $column=IF($column='$off_code','$on_code','$off_code') WHERE $key_column=$tapir_id");
    src/admin/code/update-head.php.m4:   $auth->conn->query($sql);
