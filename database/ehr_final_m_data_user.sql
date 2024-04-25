USE ehr_final;
CREATE TABLE `m_data_user` (
  `du_code` int NOT NULL AUTO_INCREMENT,
  `du_id` varchar(45) DEFAULT NULL,
  `du_name` varchar(45) DEFAULT NULL,
  `du_doj` varchar(45) DEFAULT NULL,
  `du_age` varchar(45) DEFAULT NULL,
  `du_gender` varchar(45) DEFAULT NULL,
  `du_email` varchar(45) DEFAULT NULL,
  `du_password` varchar(45) DEFAULT NULL,
  `do_code` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`du_code`)
) ;
INSERT INTO `m_data_user` VALUES (1,'himan_user','himanbabu@gmail.com','himan123','1001','102','-----	---	------\0--------------	-----\0-\0---------	---\0---------------------------	--\0-	');

