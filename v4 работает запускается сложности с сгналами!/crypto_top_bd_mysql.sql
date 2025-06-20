-- phpMyAdmin SQL Dump
-- version 5.1.1deb5ubuntu1
-- https://www.phpmyadmin.net/
--
-- Хост: localhost
-- Время создания: Июн 20 2025 г., 11:27
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
  `user_id` int NOT NULL,
  `asset` varchar(20) NOT NULL,
  `total` float NOT NULL,
  `usd_value` float DEFAULT '0',
  `free` float NOT NULL,
  `locked` float DEFAULT '0',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Дамп данных таблицы `balances`
--

INSERT INTO `balances` (`id`, `user_id`, `asset`, `total`, `usd_value`, `free`, `locked`, `updated_at`) VALUES
(1, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 06:11:56'),
(2, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 06:12:24'),
(3, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 06:40:04'),
(4, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 06:40:34'),
(5, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 06:40:52'),
(6, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 08:17:57'),
(7, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 08:18:32'),
(8, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 08:18:37'),
(9, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 08:18:41'),
(10, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 08:18:46'),
(11, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 08:18:50'),
(12, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 08:18:55'),
(13, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 08:38:12'),
(14, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 08:38:42'),
(15, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 08:38:46'),
(16, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 08:38:50'),
(17, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 08:38:56'),
(18, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 08:38:59'),
(19, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 08:39:04'),
(20, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 08:39:10'),
(21, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 09:16:04'),
(22, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 13:52:20'),
(23, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 13:53:24'),
(24, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 13:53:53'),
(25, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 13:54:04'),
(26, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 13:54:08'),
(27, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 13:54:18'),
(28, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 13:54:32'),
(29, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 13:54:35'),
(30, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 13:54:40'),
(31, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 13:54:46'),
(32, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 13:54:48'),
(33, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 13:54:51'),
(34, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 13:54:57'),
(35, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 13:55:03'),
(36, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 13:55:11'),
(37, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 13:55:17'),
(38, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 13:55:23'),
(39, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 13:55:35'),
(40, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 13:55:38'),
(41, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 13:55:42'),
(42, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 13:55:44'),
(43, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 13:55:49'),
(44, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 13:55:51'),
(45, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 14:01:06'),
(46, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 14:01:35'),
(47, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 14:01:57'),
(48, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 14:02:15'),
(49, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 14:02:45'),
(50, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 19:14:23'),
(51, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 19:15:17'),
(52, 0, 'USDT', 10000, 0, 10000, 0, '2025-06-14 19:15:20');

-- --------------------------------------------------------

--
-- Структура таблицы `bot_settings`
--

CREATE TABLE `bot_settings` (
  `id` int NOT NULL,
  `user_id` int NOT NULL,
  `strategy` varchar(50) DEFAULT 'multi_indicator',
  `risk_level` float DEFAULT '0.02',
  `max_positions` int DEFAULT '1',
  `position_size` float DEFAULT '100',
  `stop_loss_percent` float DEFAULT '2',
  `take_profit_percent` float DEFAULT '4',
  `is_active` tinyint(1) DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Структура таблицы `bot_settings_backup`
--

CREATE TABLE `bot_settings_backup` (
  `id` int NOT NULL DEFAULT '0',
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
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_heartbeat` datetime DEFAULT NULL,
  `current_strategy` varchar(50) DEFAULT NULL,
  `successful_trades` int DEFAULT '0',
  `failed_trades` int DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Дамп данных таблицы `bot_state`
--

INSERT INTO `bot_state` (`id`, `is_running`, `start_time`, `stop_time`, `total_trades`, `profitable_trades`, `total_profit`, `current_balance`, `updated_at`, `last_heartbeat`, `current_strategy`, `successful_trades`, `failed_trades`, `created_at`) VALUES
(1, 0, '2025-06-20 03:48:10', '2025-06-20 03:48:53', 0, 0, 0, 10000, '2025-06-20 03:48:53', NULL, NULL, 0, 0, '2025-06-19 06:29:48');

-- --------------------------------------------------------

--
-- Структура таблицы `bot_state_backup_20250619_092948`
--

CREATE TABLE `bot_state_backup_20250619_092948` (
  `id` int NOT NULL DEFAULT '0',
  `is_running` tinyint(1) DEFAULT '0',
  `start_time` timestamp NULL DEFAULT NULL,
  `stop_time` timestamp NULL DEFAULT NULL,
  `total_trades` int DEFAULT '0',
  `profitable_trades` int DEFAULT '0',
  `total_profit` float DEFAULT '0',
  `current_balance` float DEFAULT '0',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_heartbeat` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Дамп данных таблицы `bot_state_backup_20250619_092948`
--

INSERT INTO `bot_state_backup_20250619_092948` (`id`, `is_running`, `start_time`, `stop_time`, `total_trades`, `profitable_trades`, `total_profit`, `current_balance`, `updated_at`, `last_heartbeat`) VALUES
(1, 0, '2025-06-14 19:14:21', '2025-06-14 19:17:30', 0, 0, 0, 10000, '2025-06-14 19:17:30', NULL);

-- --------------------------------------------------------

--
-- Структура таблицы `candles`
--

CREATE TABLE `candles` (
  `id` int NOT NULL,
  `symbol` varchar(20) NOT NULL,
  `interval` varchar(10) NOT NULL,
  `open_time` datetime NOT NULL,
  `open` float NOT NULL,
  `high` float NOT NULL,
  `low` float NOT NULL,
  `close` float NOT NULL,
  `volume` float NOT NULL,
  `close_time` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Структура таблицы `market_conditions`
--

CREATE TABLE `market_conditions` (
  `id` int NOT NULL,
  `symbol` varchar(20) NOT NULL,
  `timeframe` varchar(20) NOT NULL,
  `condition_type` varchar(50) NOT NULL,
  `condition_value` varchar(50) NOT NULL,
  `strength` float DEFAULT NULL,
  `indicators` json DEFAULT NULL,
  `timestamp` timestamp NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Структура таблицы `ml_models`
--

CREATE TABLE `ml_models` (
  `id` int NOT NULL,
  `name` varchar(100) NOT NULL,
  `model_type` varchar(50) NOT NULL,
  `version` varchar(50) NOT NULL,
  `accuracy` float DEFAULT NULL,
  `precision_score` float DEFAULT NULL,
  `recall_score` float DEFAULT NULL,
  `f1_score` float DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `parameters` json DEFAULT NULL,
  `feature_importance` json DEFAULT NULL,
  `training_history` json DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT '1'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Структура таблицы `ml_predictions`
--

CREATE TABLE `ml_predictions` (
  `id` int NOT NULL,
  `model_id` int NOT NULL,
  `symbol` varchar(20) NOT NULL,
  `prediction_type` varchar(50) NOT NULL,
  `prediction_value` json NOT NULL,
  `confidence` float NOT NULL,
  `features_snapshot` json DEFAULT NULL,
  `actual_outcome` json DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Структура таблицы `news_analysis`
--

CREATE TABLE `news_analysis` (
  `id` int NOT NULL,
  `source` varchar(100) NOT NULL,
  `url` varchar(500) DEFAULT NULL,
  `title` text NOT NULL,
  `content` text,
  `summary` text,
  `sentiment_score` float DEFAULT NULL,
  `impact_score` float DEFAULT NULL,
  `relevance_score` float DEFAULT NULL,
  `affected_coins` json DEFAULT NULL,
  `entities` json DEFAULT NULL,
  `keywords` json DEFAULT NULL,
  `published_at` timestamp NULL DEFAULT NULL,
  `analyzed_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Структура таблицы `orders`
--

CREATE TABLE `orders` (
  `id` int NOT NULL,
  `user_id` int NOT NULL,
  `exchange_order_id` varchar(100) DEFAULT NULL,
  `symbol` varchar(20) NOT NULL,
  `side` varchar(10) NOT NULL,
  `type` varchar(20) NOT NULL,
  `quantity` float NOT NULL,
  `price` float DEFAULT NULL,
  `stop_price` float DEFAULT NULL,
  `status` varchar(20) NOT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

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

--
-- Дамп данных таблицы `signals`
--

INSERT INTO `signals` (`id`, `symbol`, `action`, `confidence`, `price`, `created_at`, `executed`, `stop_loss`, `take_profit`, `strategy`, `reason`, `executed_at`, `trade_id`) VALUES
(1, 'ETHUSDT', 'SELL', 0.833333, 3502.5, '2025-06-14 08:18:05', 0, 3654.3, 3274.8, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL),
(2, 'ADAUSDT', 'SELL', 0.833333, 0.71, '2025-06-14 08:18:17', 0, 0.72953, 0.680705, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL),
(3, 'ETHUSDT', 'SELL', 0.833333, 3502.5, '2025-06-14 08:18:32', 0, 3654.3, 3274.8, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL),
(4, 'ADAUSDT', 'SELL', 0.833333, 0.71, '2025-06-14 08:18:32', 0, 0.72953, 0.680705, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL),
(5, 'ETHUSDT', 'SELL', 0.833333, 3502.5, '2025-06-14 08:18:37', 0, 3654.3, 3274.8, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL),
(6, 'ADAUSDT', 'SELL', 0.833333, 0.71, '2025-06-14 08:18:37', 0, 0.72953, 0.680705, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL),
(7, 'ETHUSDT', 'SELL', 0.833333, 3502.5, '2025-06-14 08:18:41', 0, 3654.3, 3274.8, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL),
(8, 'ADAUSDT', 'SELL', 0.833333, 0.71, '2025-06-14 08:18:41', 0, 0.72953, 0.680705, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL),
(9, 'ETHUSDT', 'SELL', 0.833333, 3502.5, '2025-06-14 08:18:46', 0, 3654.3, 3274.8, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL),
(10, 'ADAUSDT', 'SELL', 0.833333, 0.71, '2025-06-14 08:18:46', 0, 0.72953, 0.680705, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL),
(11, 'ETHUSDT', 'SELL', 0.833333, 3502.5, '2025-06-14 08:18:50', 0, 3654.3, 3274.8, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL),
(12, 'ADAUSDT', 'SELL', 0.833333, 0.71, '2025-06-14 08:18:50', 0, 0.72953, 0.680705, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL),
(13, 'ETHUSDT', 'SELL', 0.833333, 3502.5, '2025-06-14 08:18:55', 0, 3654.3, 3274.8, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL),
(14, 'ADAUSDT', 'SELL', 0.833333, 0.71, '2025-06-14 08:18:56', 0, 0.72953, 0.680705, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL),
(15, 'ETHUSDT', 'SELL', 0.833333, 3444.17, '2025-06-14 08:38:23', 0, 3572.63, 3251.48, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL),
(16, 'ADAUSDT', 'BUY', 0.875, 0.71, '2025-06-14 08:38:31', 0, 0.69548, 0.73178, 'multi_indicator', 'RSI: Перепроданность; MACD: Бычье пересечение; Stochastic: Перепроданность + пересечение', NULL, NULL),
(17, 'DOTUSDT', 'BUY', 0.833333, 3.7976, '2025-06-14 08:38:39', 0, 3.66702, 3.99347, 'multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(18, 'ETHUSDT', 'SELL', 0.833333, 3444.17, '2025-06-14 08:38:42', 0, 3572.63, 3251.48, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL),
(19, 'ADAUSDT', 'BUY', 0.875, 0.71, '2025-06-14 08:38:43', 0, 0.69548, 0.73178, 'multi_indicator', 'RSI: Перепроданность; MACD: Бычье пересечение; Stochastic: Перепроданность + пересечение', NULL, NULL),
(20, 'DOTUSDT', 'BUY', 0.833333, 3.7976, '2025-06-14 08:38:43', 0, 3.66702, 3.99347, 'multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(21, 'ETHUSDT', 'SELL', 0.833333, 3444.17, '2025-06-14 08:38:46', 0, 3572.63, 3251.48, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL),
(22, 'ADAUSDT', 'BUY', 0.875, 0.71, '2025-06-14 08:38:46', 0, 0.69548, 0.73178, 'multi_indicator', 'RSI: Перепроданность; MACD: Бычье пересечение; Stochastic: Перепроданность + пересечение', NULL, NULL),
(23, 'DOTUSDT', 'BUY', 0.833333, 3.7976, '2025-06-14 08:38:46', 0, 3.66702, 3.99347, 'multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(24, 'ETHUSDT', 'SELL', 0.833333, 3444.17, '2025-06-14 08:38:50', 0, 3572.63, 3251.48, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL),
(25, 'ADAUSDT', 'BUY', 0.875, 0.71, '2025-06-14 08:38:51', 0, 0.69548, 0.73178, 'multi_indicator', 'RSI: Перепроданность; MACD: Бычье пересечение; Stochastic: Перепроданность + пересечение', NULL, NULL),
(26, 'DOTUSDT', 'BUY', 0.833333, 3.7976, '2025-06-14 08:38:51', 0, 3.66702, 3.99347, 'multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(27, 'ETHUSDT', 'SELL', 0.833333, 3444.17, '2025-06-14 08:38:56', 0, 3572.63, 3251.48, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL),
(28, 'ADAUSDT', 'BUY', 0.875, 0.71, '2025-06-14 08:38:56', 0, 0.69548, 0.73178, 'multi_indicator', 'RSI: Перепроданность; MACD: Бычье пересечение; Stochastic: Перепроданность + пересечение', NULL, NULL),
(29, 'DOTUSDT', 'BUY', 0.833333, 3.7976, '2025-06-14 08:38:56', 0, 3.66702, 3.99347, 'multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(30, 'ETHUSDT', 'SELL', 0.833333, 3444.17, '2025-06-14 08:38:59', 0, 3572.63, 3251.48, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL),
(31, 'ADAUSDT', 'BUY', 0.875, 0.71, '2025-06-14 08:38:59', 0, 0.69548, 0.73178, 'multi_indicator', 'RSI: Перепроданность; MACD: Бычье пересечение; Stochastic: Перепроданность + пересечение', NULL, NULL),
(32, 'DOTUSDT', 'BUY', 0.833333, 3.7976, '2025-06-14 08:38:59', 0, 3.66702, 3.99347, 'multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(33, 'ETHUSDT', 'SELL', 0.833333, 3444.17, '2025-06-14 08:39:04', 0, 3572.63, 3251.48, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL),
(34, 'ADAUSDT', 'BUY', 0.875, 0.71, '2025-06-14 08:39:04', 0, 0.69548, 0.73178, 'multi_indicator', 'RSI: Перепроданность; MACD: Бычье пересечение; Stochastic: Перепроданность + пересечение', NULL, NULL),
(35, 'DOTUSDT', 'BUY', 0.833333, 3.7976, '2025-06-14 08:39:04', 0, 3.66702, 3.99347, 'multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(36, 'ETHUSDT', 'SELL', 0.833333, 3444.17, '2025-06-14 08:39:10', 0, 3572.63, 3251.48, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL),
(37, 'ADAUSDT', 'BUY', 0.875, 0.71, '2025-06-14 08:39:10', 0, 0.69548, 0.73178, 'multi_indicator', 'RSI: Перепроданность; MACD: Бычье пересечение; Stochastic: Перепроданность + пересечение', NULL, NULL),
(38, 'DOTUSDT', 'BUY', 0.833333, 3.7976, '2025-06-14 08:39:10', 0, 3.66702, 3.99347, 'multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(39, 'BNBUSDT', 'BUY', 0.833333, 717, '2025-06-14 13:52:33', 0, 681.15, 788.7, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(40, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:53:18', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(41, 'BNBUSDT', 'BUY', 0.833333, 717, '2025-06-14 13:53:24', 0, 681.15, 788.7, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(42, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:53:51', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(43, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:54:02', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(44, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:54:04', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(45, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:54:15', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(46, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:54:26', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(47, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:54:32', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(48, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:54:35', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(49, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:54:40', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(50, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:54:46', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(51, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:54:48', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(52, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:54:51', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(53, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:54:57', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(54, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:55:09', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(55, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:55:11', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(56, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:55:21', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(57, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:55:29', 0, 3.51706, 3.56441, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(58, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:55:35', 0, 3.51706, 3.56441, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(59, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:55:38', 0, 3.51706, 3.56441, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(60, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:55:42', 0, 3.51706, 3.56441, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(61, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:55:44', 0, 3.51706, 3.56441, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(62, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:55:49', 0, 3.51706, 3.56441, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(63, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:55:51', 0, 3.51706, 3.56441, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(64, 'BNBUSDT', 'BUY', 0.833333, 710, '2025-06-14 14:01:17', 0, 674.5, 781, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(65, 'XRPUSDT', 'BUY', 0.833333, 3.5392, '2025-06-14 14:01:52', 0, 3.52119, 3.56622, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(66, 'BNBUSDT', 'BUY', 0.833333, 710, '2025-06-14 14:01:57', 0, 674.5, 781, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(67, 'XRPUSDT', 'BUY', 0.833333, 3.5392, '2025-06-14 14:02:10', 0, 3.52119, 3.56622, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(68, 'BNBUSDT', 'BUY', 0.833333, 710, '2025-06-14 14:02:23', 0, 674.5, 781, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(69, 'XRPUSDT', 'BUY', 0.833333, 3.5392, '2025-06-14 14:02:40', 0, 3.52119, 3.56622, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(70, 'BNBUSDT', 'BUY', 0.833333, 710, '2025-06-14 14:02:45', 0, 674.5, 781, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL);

-- --------------------------------------------------------

--
-- Структура таблицы `social_signals`
--

CREATE TABLE `social_signals` (
  `id` int NOT NULL,
  `platform` varchar(50) NOT NULL,
  `author` varchar(100) DEFAULT NULL,
  `author_followers` int DEFAULT NULL,
  `content` text NOT NULL,
  `url` varchar(500) DEFAULT NULL,
  `sentiment` float DEFAULT NULL,
  `influence_score` float DEFAULT NULL,
  `engagement_score` float DEFAULT NULL,
  `mentioned_coins` json DEFAULT NULL,
  `hashtags` json DEFAULT NULL,
  `is_verified_author` tinyint(1) DEFAULT '0',
  `created_at` timestamp NULL DEFAULT NULL,
  `collected_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Структура таблицы `strategy_performance`
--

CREATE TABLE `strategy_performance` (
  `id` int NOT NULL,
  `strategy_name` varchar(100) NOT NULL,
  `symbol` varchar(20) NOT NULL,
  `market_condition` varchar(50) NOT NULL,
  `timeframe` varchar(20) NOT NULL,
  `win_rate` float NOT NULL,
  `avg_profit` float NOT NULL,
  `avg_loss` float NOT NULL,
  `profit_factor` float DEFAULT NULL,
  `sharpe_ratio` float DEFAULT NULL,
  `max_drawdown` float DEFAULT NULL,
  `total_trades` int NOT NULL,
  `period_start` timestamp NOT NULL,
  `period_end` timestamp NOT NULL,
  `metrics` json DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Структура таблицы `trades`
--

CREATE TABLE `trades` (
  `id` int NOT NULL,
  `symbol` varchar(20) NOT NULL,
  `side` varchar(10) NOT NULL,
  `price` float NOT NULL,
  `total` float NOT NULL DEFAULT '0',
  `close_price` float DEFAULT NULL,
  `quantity` float NOT NULL,
  `profit_loss` float DEFAULT NULL,
  `status` varchar(20) NOT NULL DEFAULT 'OPEN',
  `order_id` varchar(100) DEFAULT NULL,
  `strategy` varchar(50) NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `close_time` timestamp NULL DEFAULT NULL,
  `stop_loss` float DEFAULT NULL,
  `take_profit` float DEFAULT NULL,
  `profit_loss_percent` float DEFAULT NULL,
  `trailing_stop` tinyint(1) DEFAULT '0',
  `fee` float DEFAULT '0',
  `fee_asset` varchar(10) DEFAULT NULL,
  `notes` text,
  `user_id` int DEFAULT NULL COMMENT 'ID пользователя (может быть NULL для старых записей)',
  `signal_id` int DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Структура таблицы `trade_ml_predictions`
--

CREATE TABLE `trade_ml_predictions` (
  `trade_id` int NOT NULL,
  `prediction_id` int NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Структура таблицы `trading_logs`
--

CREATE TABLE `trading_logs` (
  `id` int NOT NULL,
  `log_level` varchar(20) NOT NULL,
  `category` varchar(50) NOT NULL,
  `message` text NOT NULL,
  `context` json DEFAULT NULL,
  `symbol` varchar(20) DEFAULT NULL,
  `strategy` varchar(50) DEFAULT NULL,
  `trade_id` int DEFAULT NULL,
  `signal_id` int DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Структура таблицы `trading_pairs`
--

CREATE TABLE `trading_pairs` (
  `id` int NOT NULL,
  `symbol` varchar(20) NOT NULL,
  `base_asset` varchar(10) DEFAULT NULL,
  `quote_asset` varchar(10) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT '1',
  `min_position_size` float DEFAULT NULL,
  `max_position_size` float DEFAULT NULL,
  `strategy` varchar(50) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `stop_loss_percent` float DEFAULT '2',
  `take_profit_percent` float DEFAULT '4',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `min_order_size` float DEFAULT NULL,
  `max_order_size` float DEFAULT NULL,
  `price_precision` int DEFAULT NULL,
  `quantity_precision` int DEFAULT NULL,
  `status` varchar(20) DEFAULT 'TRADING'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Дамп данных таблицы `trading_pairs`
--

INSERT INTO `trading_pairs` (`id`, `symbol`, `base_asset`, `quote_asset`, `is_active`, `min_position_size`, `max_position_size`, `strategy`, `created_at`, `stop_loss_percent`, `take_profit_percent`, `updated_at`, `min_order_size`, `max_order_size`, `price_precision`, `quantity_precision`, `status`) VALUES
(1, 'BTCUSDT', 'BTC', 'USDT', 1, NULL, NULL, 'conservative', '2025-06-13 11:13:12', 1, 3, '2025-06-20 05:02:18', NULL, NULL, NULL, NULL, 'TRADING'),
(2, 'ETHUSDT', 'ETH', 'USDT', 1, NULL, NULL, 'conservative', '2025-06-13 11:13:12', 1, 3, '2025-06-20 05:02:18', NULL, NULL, NULL, NULL, 'TRADING'),
(3, 'BNBUSDT', 'BNB', 'USDT', 0, NULL, NULL, 'safe_multi_indicator', '2025-06-13 11:13:12', 1.5, 3, '2025-06-20 05:02:18', NULL, NULL, NULL, NULL, 'TRADING'),
(4, 'SOLUSDT', 'SOL', 'USDT', 0, NULL, NULL, 'safe_multi_indicator', '2025-06-13 11:13:12', 1.5, 3, '2025-06-20 05:02:18', NULL, NULL, NULL, NULL, 'TRADING'),
(5, 'ADAUSDT', 'ADA', 'USDT', 0, NULL, NULL, 'safe_multi_indicator', '2025-06-13 10:07:12', 1.5, 3, '2025-06-20 05:02:18', NULL, NULL, NULL, NULL, 'TRADING'),
(6, 'DOGEUSDT', 'DOGE', 'USDT', 0, NULL, NULL, 'safe_multi_indicator', '2025-06-13 10:07:12', 1.5, 3, '2025-06-20 05:02:18', NULL, NULL, NULL, NULL, 'TRADING'),
(7, 'XRPUSDT', 'XRP', 'USDT', 0, NULL, NULL, 'safe_multi_indicator', '2025-06-13 10:07:12', 1.5, 3, '2025-06-20 05:02:18', NULL, NULL, NULL, NULL, 'TRADING'),
(8, 'DOTUSDT', 'DOT', 'USDT', 0, NULL, NULL, 'safe_multi_indicator', '2025-06-13 10:07:12', 1.5, 3, '2025-06-20 05:02:18', NULL, NULL, NULL, NULL, 'TRADING');

-- --------------------------------------------------------

--
-- Структура таблицы `users`
--

CREATE TABLE `users` (
  `id` int NOT NULL,
  `username` varchar(50) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `is_active` tinyint(1) DEFAULT '1',
  `is_blocked` tinyint(1) DEFAULT '0',
  `failed_login_attempts` int DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `last_login` timestamp NULL DEFAULT NULL,
  `blocked_at` timestamp NULL DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `is_admin` tinyint(1) DEFAULT '0',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Дамп данных таблицы `users`
--

INSERT INTO `users` (`id`, `username`, `password_hash`, `is_active`, `is_blocked`, `failed_login_attempts`, `created_at`, `last_login`, `blocked_at`, `email`, `is_admin`, `updated_at`) VALUES
(1, 'WaySenCryptoTop', '$2b$12$Hrv3wXuwXczSXwVOCUTG9.6523svqV8TWNG50qX4Fp9Pgb4Mml6oy', 1, 0, 0, '2025-06-13 08:21:55', '2025-06-19 16:34:22', NULL, NULL, 1, '2025-06-19 16:34:22');

--
-- Индексы сохранённых таблиц
--

--
-- Индексы таблицы `balances`
--
ALTER TABLE `balances`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_currency` (`asset`),
  ADD KEY `idx_timestamp` (`updated_at`),
  ADD KEY `idx_currency_timestamp` (`asset`,`updated_at`);

--
-- Индексы таблицы `bot_settings`
--
ALTER TABLE `bot_settings`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_user_settings` (`user_id`);

--
-- Индексы таблицы `bot_state`
--
ALTER TABLE `bot_state`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_updated_at` (`updated_at`);

--
-- Индексы таблицы `candles`
--
ALTER TABLE `candles`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `idx_candle_symbol_time` (`symbol`,`interval`,`open_time`);

--
-- Индексы таблицы `market_conditions`
--
ALTER TABLE `market_conditions`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_symbol_timestamp` (`symbol`,`timestamp`),
  ADD KEY `idx_condition_type` (`condition_type`);

--
-- Индексы таблицы `ml_models`
--
ALTER TABLE `ml_models`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_name_version` (`name`,`version`),
  ADD KEY `idx_model_type` (`model_type`),
  ADD KEY `idx_is_active` (`is_active`);

--
-- Индексы таблицы `ml_predictions`
--
ALTER TABLE `ml_predictions`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_model_symbol` (`model_id`,`symbol`),
  ADD KEY `idx_created_at` (`created_at`);

--
-- Индексы таблицы `news_analysis`
--
ALTER TABLE `news_analysis`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_source_published` (`source`,`published_at`),
  ADD KEY `idx_sentiment` (`sentiment_score`),
  ADD KEY `idx_impact` (`impact_score`);
ALTER TABLE `news_analysis` ADD FULLTEXT KEY `idx_title_content` (`title`,`content`);

--
-- Индексы таблицы `orders`
--
ALTER TABLE `orders`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `exchange_order_id` (`exchange_order_id`),
  ADD KEY `user_id` (`user_id`);

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
-- Индексы таблицы `social_signals`
--
ALTER TABLE `social_signals`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_platform_created` (`platform`,`created_at`),
  ADD KEY `idx_author` (`author`),
  ADD KEY `idx_influence` (`influence_score`);
ALTER TABLE `social_signals` ADD FULLTEXT KEY `idx_content` (`content`);

--
-- Индексы таблицы `strategy_performance`
--
ALTER TABLE `strategy_performance`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_strategy_symbol` (`strategy_name`,`symbol`),
  ADD KEY `idx_period` (`period_start`,`period_end`),
  ADD KEY `idx_market_condition` (`market_condition`);

--
-- Индексы таблицы `trades`
--
ALTER TABLE `trades`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_symbol` (`symbol`),
  ADD KEY `idx_status` (`status`),
  ADD KEY `idx_created_at` (`created_at`),
  ADD KEY `idx_closed_at` (`close_time`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `signal_id` (`signal_id`);

--
-- Индексы таблицы `trade_ml_predictions`
--
ALTER TABLE `trade_ml_predictions`
  ADD PRIMARY KEY (`trade_id`,`prediction_id`),
  ADD KEY `prediction_id` (`prediction_id`);

--
-- Индексы таблицы `trading_logs`
--
ALTER TABLE `trading_logs`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_level_category` (`log_level`,`category`),
  ADD KEY `idx_created_at` (`created_at`),
  ADD KEY `idx_symbol` (`symbol`),
  ADD KEY `idx_trade_id` (`trade_id`);

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
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=53;

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
-- AUTO_INCREMENT для таблицы `candles`
--
ALTER TABLE `candles`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT для таблицы `market_conditions`
--
ALTER TABLE `market_conditions`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT для таблицы `ml_models`
--
ALTER TABLE `ml_models`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT для таблицы `ml_predictions`
--
ALTER TABLE `ml_predictions`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT для таблицы `news_analysis`
--
ALTER TABLE `news_analysis`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT для таблицы `orders`
--
ALTER TABLE `orders`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT для таблицы `signals`
--
ALTER TABLE `signals`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=71;

--
-- AUTO_INCREMENT для таблицы `social_signals`
--
ALTER TABLE `social_signals`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT для таблицы `strategy_performance`
--
ALTER TABLE `strategy_performance`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT для таблицы `trades`
--
ALTER TABLE `trades`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT для таблицы `trading_logs`
--
ALTER TABLE `trading_logs`
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

--
-- Ограничения внешнего ключа сохраненных таблиц
--

--
-- Ограничения внешнего ключа таблицы `bot_settings`
--
ALTER TABLE `bot_settings`
  ADD CONSTRAINT `bot_settings_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Ограничения внешнего ключа таблицы `ml_predictions`
--
ALTER TABLE `ml_predictions`
  ADD CONSTRAINT `ml_predictions_ibfk_1` FOREIGN KEY (`model_id`) REFERENCES `ml_models` (`id`);

--
-- Ограничения внешнего ключа таблицы `orders`
--
ALTER TABLE `orders`
  ADD CONSTRAINT `orders_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

--
-- Ограничения внешнего ключа таблицы `trades`
--
ALTER TABLE `trades`
  ADD CONSTRAINT `trades_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  ADD CONSTRAINT `trades_ibfk_2` FOREIGN KEY (`signal_id`) REFERENCES `signals` (`id`);

--
-- Ограничения внешнего ключа таблицы `trade_ml_predictions`
--
ALTER TABLE `trade_ml_predictions`
  ADD CONSTRAINT `trade_ml_predictions_ibfk_1` FOREIGN KEY (`trade_id`) REFERENCES `trades` (`id`),
  ADD CONSTRAINT `trade_ml_predictions_ibfk_2` FOREIGN KEY (`prediction_id`) REFERENCES `ml_predictions` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
