SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;


CREATE TABLE `dictionary` (
  `id` varchar(20) NOT NULL,
  `word` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `meaning` text CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `length` tinyint(4) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;

CREATE TABLE `guess` (
  `platform` varchar(5) NOT NULL,
  `userid` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_bin NOT NULL,
  `guess` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `word` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `meaning` text CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

CREATE TABLE `log` (
  `logid` int(11) NOT NULL,
  `platform` varchar(5) NOT NULL,
  `userid` varchar(255) NOT NULL,
  `message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `time` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;

CREATE TABLE `tggroupbotmsg` (
  `userid` varchar(20) NOT NULL,
  `messageid` varchar(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;

CREATE TABLE `tggrouplimit` (
  `userid` varchar(20) NOT NULL,
  `fromid` varchar(20) NOT NULL,
  `type` varchar(10) NOT NULL,
  `date` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_bin;


ALTER TABLE `dictionary`
  ADD UNIQUE KEY `id` (`id`),
  ADD KEY `length` (`length`),
  ADD KEY `word` (`word`);

ALTER TABLE `guess`
  ADD PRIMARY KEY (`platform`,`userid`);

ALTER TABLE `log`
  ADD PRIMARY KEY (`logid`),
  ADD KEY `time` (`time`);

ALTER TABLE `tggroupbotmsg`
  ADD KEY `userid` (`userid`);

ALTER TABLE `tggrouplimit`
  ADD KEY `userid` (`userid`,`fromid`,`type`),
  ADD KEY `date` (`date`);


ALTER TABLE `log`
  MODIFY `logid` int(11) NOT NULL AUTO_INCREMENT;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
