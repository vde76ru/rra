-- phpMyAdmin SQL Dump
-- version 5.1.1deb5ubuntu1
-- https://www.phpmyadmin.net/
--
-- Хост: localhost
-- Время создания: Июн 14 2025 г., 09:08
-- Версия сервера: 8.0.42-0ubuntu0.22.04.1
-- Версия PHP: 8.1.2-1ubuntu2.21

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- База данных: `crypto_top_bd_mysql`
--

-- --------------------------------------------------------

--
-- Структура таблицы `balances`
--

CREATE TABLE `balances` (
  `id` int NOT NULL,
  `currency` varchar(10) NOT NULL,
  `total` float NOT NULL,
  `free` float NOT NULL,
  `used` float NOT NULL,
  `timestamp` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Структура таблицы `bot_settings`
--

CREATE TABLE `bot_settings` (
  `id` int NOT NULL,
  `key` varchar(50) NOT NULL,
  `value` text,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `description` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Структура таблицы `bot_state`
--

CREATE TABLE `bot_state` (
  `id` int NOT NULL,
  `is_running` tinyint(1) DEFAULT '0',
  `start_time` timestamp NULL DEFAULT NULL,
  `stop_time` timestamp NULL DEFAULT NULL,
  `total_trades` int DEFAULT '0',
  `profitable_trades` int DEFAULT '0',
  `total_profit` float DEFAULT '0',
  `current_balance` float DEFAULT '0',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Дамп данных таблицы `bot_state`
--

INSERT INTO `bot_state` (`id`, `is_running`, `start_time`, `stop_time`, `total_trades`, `profitable_trades`, `total_profit`, `current_balance`, `updated_at`) VALUES
(1, 0, '2025-06-13 12:16:41', '2025-06-13 12:16:43', 0, 0, 0, 10000, '2025-06-13 12:16:43');

-- --------------------------------------------------------

--
-- Структура таблицы `signals`
--

CREATE TABLE `signals` (
  `id` int NOT NULL,
  `symbol` varchar(20) NOT NULL,
  `action` varchar(10) NOT NULL,
  `confidence` float NOT NULL,
  `price` float NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `executed` tinyint(1) DEFAULT '0',
  `stop_loss` float DEFAULT NULL,
  `take_profit` float DEFAULT NULL,
  `strategy` varchar(50) DEFAULT NULL,
  `reason` text,
  `executed_at` timestamp NULL DEFAULT NULL,
  `trade_id` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Структура таблицы `trades`
--

CREATE TABLE `trades` (
  `id` int NOT NULL,
  `symbol` varchar(20) NOT NULL,
  `side` varchar(10) NOT NULL,
  `entry_price` float NOT NULL,
  `exit_price` float DEFAULT NULL,
  `quantity` float NOT NULL,
  `profit` float DEFAULT NULL,
  `status` varchar(20) NOT NULL DEFAULT 'OPEN',
  `strategy` varchar(50) NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `closed_at` timestamp NULL DEFAULT NULL,
  `stop_loss` float DEFAULT NULL,
  `take_profit` float DEFAULT NULL,
  `profit_percent` float DEFAULT NULL,
  `trailing_stop` tinyint(1) DEFAULT '0',
  `commission` float DEFAULT '0',
  `notes` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Структура таблицы `trading_pairs`
--

CREATE TABLE `trading_pairs` (
  `id` int NOT NULL,
  `symbol` varchar(20) NOT NULL,
  `is_active` tinyint(1) DEFAULT '1',
  `min_position_size` float DEFAULT NULL,
  `max_position_size` float DEFAULT NULL,
  `strategy` varchar(50) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `stop_loss_percent` float DEFAULT '2',
  `take_profit_percent` float DEFAULT '4',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Дамп данных таблицы `trading_pairs`
--

INSERT INTO `trading_pairs` (`id`, `symbol`, `is_active`, `min_position_size`, `max_position_size`, `strategy`, `created_at`, `stop_loss_percent`, `take_profit_percent`, `updated_at`) VALUES
(1, 'BTCUSDT', 1, NULL, NULL, 'multi_indicator', '2025-06-13 11:13:12', 2, 4, '2025-06-13 11:48:03'),
(2, 'ETHUSDT', 1, NULL, NULL, 'multi_indicator', '2025-06-13 11:13:12', 2, 4, '2025-06-13 11:48:03'),
(3, 'BNBUSDT', 1, NULL, NULL, 'multi_indicator', '2025-06-13 11:13:12', 2, 4, '2025-06-13 11:48:03'),
(4, 'SOLUSDT', 1, NULL, NULL, 'multi_indicator', '2025-06-13 11:13:12', 2, 4, '2025-06-13 11:48:03'),
(5, 'ADAUSDT', 1, NULL, NULL, 'multi_indicator', '2025-06-13 10:07:12', 2, 4, '2025-06-13 11:48:03'),
(6, 'DOGEUSDT', 1, NULL, NULL, 'multi_indicator', '2025-06-13 10:07:12', 2, 4, '2025-06-13 11:48:03'),
(7, 'XRPUSDT', 1, NULL, NULL, 'multi_indicator', '2025-06-13 10:07:12', 2, 4, '2025-06-13 11:48:03'),
(8, 'DOTUSDT', 1, NULL, NULL, 'multi_indicator', '2025-06-13 10:07:12', 2, 4, '2025-06-13 11:48:03');

-- --------------------------------------------------------

--
-- Структура таблицы `users`
--

CREATE TABLE `users` (
  `id` int NOT NULL,
  `username` varchar(50) NOT NULL,
  `hashed_password` varchar(128) NOT NULL,
  `is_active` tinyint(1) DEFAULT '1',
  `is_blocked` tinyint(1) DEFAULT '0',
  `failed_login_attempts` int DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `last_login` timestamp NULL DEFAULT NULL,
  `blocked_at` timestamp NULL DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `is_admin` tinyint(1) DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Дамп данных таблицы `users`
--

INSERT INTO `users` (`id`, `username`, `hashed_password`, `is_active`, `is_blocked`, `failed_login_attempts`, `created_at`, `last_login`, `blocked_at`, `email`, `is_admin`) VALUES
(1, 'WaySenCryptoTop', '$2b$12$Hrv3wXuwXczSXwVOCUTG9.6523svqV8TWNG50qX4Fp9Pgb4Mml6oy', 1, 0, 0, '2025-06-13 08:21:55', '2025-06-13 12:23:10', NULL, NULL, 0);

--
-- Индексы сохранённых таблиц
--

--
-- Индексы таблицы `balances`
--
ALTER TABLE `balances`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_currency` (`currency`),
  ADD KEY `idx_timestamp` (`timestamp`),
  ADD KEY `idx_currency_timestamp` (`currency`,`timestamp`);

--
-- Индексы таблицы `bot_settings`
--
ALTER TABLE `bot_settings`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `key` (`key`),
  ADD KEY `idx_key` (`key`);

--
-- Индексы таблицы `bot_state`
--
ALTER TABLE `bot_state`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_updated_at` (`updated_at`);

--
-- Индексы таблицы `signals`
--
ALTER TABLE `signals`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_symbol` (`symbol`),
  ADD KEY `idx_created_at` (`created_at`),
  ADD KEY `idx_executed` (`executed`),
  ADD KEY `idx_strategy` (`strategy`);

--
-- Индексы таблицы `trades`
--
ALTER TABLE `trades`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_symbol` (`symbol`),
  ADD KEY `idx_status` (`status`),
  ADD KEY `idx_created_at` (`created_at`),
  ADD KEY `idx_closed_at` (`closed_at`);

--
-- Индексы таблицы `trading_pairs`
--
ALTER TABLE `trading_pairs`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `symbol` (`symbol`),
  ADD KEY `idx_symbol` (`symbol`);

--
-- Индексы таблицы `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`),
  ADD KEY `idx_username` (`username`);

--
-- AUTO_INCREMENT для сохранённых таблиц
--

--
-- AUTO_INCREMENT для таблицы `balances`
--
ALTER TABLE `balances`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT для таблицы `bot_settings`
--
ALTER TABLE `bot_settings`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT для таблицы `bot_state`
--
ALTER TABLE `bot_state`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT для таблицы `signals`
--
ALTER TABLE `signals`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT для таблицы `trades`
--
ALTER TABLE `trades`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT для таблицы `trading_pairs`
--
ALTER TABLE `trading_pairs`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT для таблицы `users`
--
ALTER TABLE `users`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
