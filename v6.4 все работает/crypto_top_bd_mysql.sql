-- phpMyAdmin SQL Dump
-- version 5.1.1deb5ubuntu1
-- https://www.phpmyadmin.net/
--
-- Хост: localhost
-- Время создания: Июн 21 2025 г., 17:43
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
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `active_pairs` json DEFAULT NULL COMMENT 'Активные торговые пары',
  `cycles_count` int DEFAULT '0' COMMENT 'Количество циклов анализа',
  `trades_today` int DEFAULT '0' COMMENT 'Сделок сегодня',
  `last_error` text COMMENT 'Последняя ошибка',
  `status` varchar(20) DEFAULT 'stopped' COMMENT 'Статус бота'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Дамп данных таблицы `bot_state`
--

INSERT INTO `bot_state` (`id`, `is_running`, `start_time`, `stop_time`, `total_trades`, `profitable_trades`, `total_profit`, `current_balance`, `updated_at`, `last_heartbeat`, `current_strategy`, `successful_trades`, `failed_trades`, `created_at`, `active_pairs`, `cycles_count`, `trades_today`, `last_error`, `status`) VALUES
(1, 1, '2025-06-20 13:48:58', NULL, 0, 0, 0, 10000, '2025-06-20 13:48:58', NULL, NULL, 0, 0, '2025-06-19 06:29:48', NULL, 0, 0, NULL, 'stopped');

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
  `is_executed` tinyint(1) DEFAULT '0' COMMENT 'Флаг выполнения сигнала',
  `stop_loss` float DEFAULT NULL,
  `take_profit` float DEFAULT NULL,
  `strategy` varchar(50) DEFAULT NULL,
  `reason` text,
  `executed_at` timestamp NULL DEFAULT NULL,
  `trade_id` int DEFAULT NULL,
  `indicators` json DEFAULT NULL COMMENT 'JSON данные с индикаторами, stop_loss, take_profit и другими метриками'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Дамп данных таблицы `signals`
--

INSERT INTO `signals` (`id`, `symbol`, `action`, `confidence`, `price`, `created_at`, `is_executed`, `stop_loss`, `take_profit`, `strategy`, `reason`, `executed_at`, `trade_id`, `indicators`) VALUES
(1, 'ETHUSDT', 'SELL', 0.833333, 3502.5, '2025-06-14 08:18:05', 0, 3654.3, 3274.8, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL, '{\"stop_loss\": 3654.2998046875, \"take_profit\": 3274.800537109375, \"migrated_from_columns\": true}'),
(2, 'ADAUSDT', 'SELL', 0.833333, 0.71, '2025-06-14 08:18:17', 0, 0.72953, 0.680705, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL, '{\"stop_loss\": 0.7295300364494324, \"take_profit\": 0.6807050108909607, \"migrated_from_columns\": true}'),
(3, 'ETHUSDT', 'SELL', 0.833333, 3502.5, '2025-06-14 08:18:32', 0, 3654.3, 3274.8, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL, '{\"stop_loss\": 3654.2998046875, \"take_profit\": 3274.800537109375, \"migrated_from_columns\": true}'),
(4, 'ADAUSDT', 'SELL', 0.833333, 0.71, '2025-06-14 08:18:32', 0, 0.72953, 0.680705, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL, '{\"stop_loss\": 0.7295300364494324, \"take_profit\": 0.6807050108909607, \"migrated_from_columns\": true}'),
(5, 'ETHUSDT', 'SELL', 0.833333, 3502.5, '2025-06-14 08:18:37', 0, 3654.3, 3274.8, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL, '{\"stop_loss\": 3654.2998046875, \"take_profit\": 3274.800537109375, \"migrated_from_columns\": true}'),
(6, 'ADAUSDT', 'SELL', 0.833333, 0.71, '2025-06-14 08:18:37', 0, 0.72953, 0.680705, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL, '{\"stop_loss\": 0.7295300364494324, \"take_profit\": 0.6807050108909607, \"migrated_from_columns\": true}'),
(7, 'ETHUSDT', 'SELL', 0.833333, 3502.5, '2025-06-14 08:18:41', 0, 3654.3, 3274.8, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL, '{\"stop_loss\": 3654.2998046875, \"take_profit\": 3274.800537109375, \"migrated_from_columns\": true}'),
(8, 'ADAUSDT', 'SELL', 0.833333, 0.71, '2025-06-14 08:18:41', 0, 0.72953, 0.680705, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL, '{\"stop_loss\": 0.7295300364494324, \"take_profit\": 0.6807050108909607, \"migrated_from_columns\": true}'),
(9, 'ETHUSDT', 'SELL', 0.833333, 3502.5, '2025-06-14 08:18:46', 0, 3654.3, 3274.8, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL, '{\"stop_loss\": 3654.2998046875, \"take_profit\": 3274.800537109375, \"migrated_from_columns\": true}'),
(10, 'ADAUSDT', 'SELL', 0.833333, 0.71, '2025-06-14 08:18:46', 0, 0.72953, 0.680705, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL, '{\"stop_loss\": 0.7295300364494324, \"take_profit\": 0.6807050108909607, \"migrated_from_columns\": true}'),
(11, 'ETHUSDT', 'SELL', 0.833333, 3502.5, '2025-06-14 08:18:50', 0, 3654.3, 3274.8, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL, '{\"stop_loss\": 3654.2998046875, \"take_profit\": 3274.800537109375, \"migrated_from_columns\": true}'),
(12, 'ADAUSDT', 'SELL', 0.833333, 0.71, '2025-06-14 08:18:50', 0, 0.72953, 0.680705, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL, '{\"stop_loss\": 0.7295300364494324, \"take_profit\": 0.6807050108909607, \"migrated_from_columns\": true}'),
(13, 'ETHUSDT', 'SELL', 0.833333, 3502.5, '2025-06-14 08:18:55', 0, 3654.3, 3274.8, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL, '{\"stop_loss\": 3654.2998046875, \"take_profit\": 3274.800537109375, \"migrated_from_columns\": true}'),
(14, 'ADAUSDT', 'SELL', 0.833333, 0.71, '2025-06-14 08:18:56', 0, 0.72953, 0.680705, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL, '{\"stop_loss\": 0.7295300364494324, \"take_profit\": 0.6807050108909607, \"migrated_from_columns\": true}'),
(15, 'ETHUSDT', 'SELL', 0.833333, 3444.17, '2025-06-14 08:38:23', 0, 3572.63, 3251.48, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL, '{\"stop_loss\": 3572.63134765625, \"take_profit\": 3251.478271484375, \"migrated_from_columns\": true}'),
(16, 'ADAUSDT', 'BUY', 0.875, 0.71, '2025-06-14 08:38:31', 0, 0.69548, 0.73178, 'multi_indicator', 'RSI: Перепроданность; MACD: Бычье пересечение; Stochastic: Перепроданность + пересечение', NULL, NULL, '{\"stop_loss\": 0.6954801082611084, \"take_profit\": 0.7317798733711243, \"migrated_from_columns\": true}'),
(17, 'DOTUSDT', 'BUY', 0.833333, 3.7976, '2025-06-14 08:38:39', 0, 3.66702, 3.99347, 'multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL, '{\"stop_loss\": 3.6670217514038086, \"take_profit\": 3.9934675693511963, \"migrated_from_columns\": true}'),
(18, 'ETHUSDT', 'SELL', 0.833333, 3444.17, '2025-06-14 08:38:42', 0, 3572.63, 3251.48, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL, '{\"stop_loss\": 3572.63134765625, \"take_profit\": 3251.478271484375, \"migrated_from_columns\": true}'),
(19, 'ADAUSDT', 'BUY', 0.875, 0.71, '2025-06-14 08:38:43', 0, 0.69548, 0.73178, 'multi_indicator', 'RSI: Перепроданность; MACD: Бычье пересечение; Stochastic: Перепроданность + пересечение', NULL, NULL, '{\"stop_loss\": 0.6954801082611084, \"take_profit\": 0.7317798733711243, \"migrated_from_columns\": true}'),
(20, 'DOTUSDT', 'BUY', 0.833333, 3.7976, '2025-06-14 08:38:43', 0, 3.66702, 3.99347, 'multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL, '{\"stop_loss\": 3.6670217514038086, \"take_profit\": 3.9934675693511963, \"migrated_from_columns\": true}'),
(21, 'ETHUSDT', 'SELL', 0.833333, 3444.17, '2025-06-14 08:38:46', 0, 3572.63, 3251.48, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL, '{\"stop_loss\": 3572.63134765625, \"take_profit\": 3251.478271484375, \"migrated_from_columns\": true}'),
(22, 'ADAUSDT', 'BUY', 0.875, 0.71, '2025-06-14 08:38:46', 0, 0.69548, 0.73178, 'multi_indicator', 'RSI: Перепроданность; MACD: Бычье пересечение; Stochastic: Перепроданность + пересечение', NULL, NULL, '{\"stop_loss\": 0.6954801082611084, \"take_profit\": 0.7317798733711243, \"migrated_from_columns\": true}'),
(23, 'DOTUSDT', 'BUY', 0.833333, 3.7976, '2025-06-14 08:38:46', 0, 3.66702, 3.99347, 'multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL, '{\"stop_loss\": 3.6670217514038086, \"take_profit\": 3.9934675693511963, \"migrated_from_columns\": true}'),
(24, 'ETHUSDT', 'SELL', 0.833333, 3444.17, '2025-06-14 08:38:50', 0, 3572.63, 3251.48, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL, '{\"stop_loss\": 3572.63134765625, \"take_profit\": 3251.478271484375, \"migrated_from_columns\": true}'),
(25, 'ADAUSDT', 'BUY', 0.875, 0.71, '2025-06-14 08:38:51', 0, 0.69548, 0.73178, 'multi_indicator', 'RSI: Перепроданность; MACD: Бычье пересечение; Stochastic: Перепроданность + пересечение', NULL, NULL, '{\"stop_loss\": 0.6954801082611084, \"take_profit\": 0.7317798733711243, \"migrated_from_columns\": true}'),
(26, 'DOTUSDT', 'BUY', 0.833333, 3.7976, '2025-06-14 08:38:51', 0, 3.66702, 3.99347, 'multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL, '{\"stop_loss\": 3.6670217514038086, \"take_profit\": 3.9934675693511963, \"migrated_from_columns\": true}'),
(27, 'ETHUSDT', 'SELL', 0.833333, 3444.17, '2025-06-14 08:38:56', 0, 3572.63, 3251.48, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL, '{\"stop_loss\": 3572.63134765625, \"take_profit\": 3251.478271484375, \"migrated_from_columns\": true}'),
(28, 'ADAUSDT', 'BUY', 0.875, 0.71, '2025-06-14 08:38:56', 0, 0.69548, 0.73178, 'multi_indicator', 'RSI: Перепроданность; MACD: Бычье пересечение; Stochastic: Перепроданность + пересечение', NULL, NULL, '{\"stop_loss\": 0.6954801082611084, \"take_profit\": 0.7317798733711243, \"migrated_from_columns\": true}'),
(29, 'DOTUSDT', 'BUY', 0.833333, 3.7976, '2025-06-14 08:38:56', 0, 3.66702, 3.99347, 'multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL, '{\"stop_loss\": 3.6670217514038086, \"take_profit\": 3.9934675693511963, \"migrated_from_columns\": true}'),
(30, 'ETHUSDT', 'SELL', 0.833333, 3444.17, '2025-06-14 08:38:59', 0, 3572.63, 3251.48, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL, '{\"stop_loss\": 3572.63134765625, \"take_profit\": 3251.478271484375, \"migrated_from_columns\": true}'),
(31, 'ADAUSDT', 'BUY', 0.875, 0.71, '2025-06-14 08:38:59', 0, 0.69548, 0.73178, 'multi_indicator', 'RSI: Перепроданность; MACD: Бычье пересечение; Stochastic: Перепроданность + пересечение', NULL, NULL, '{\"stop_loss\": 0.6954801082611084, \"take_profit\": 0.7317798733711243, \"migrated_from_columns\": true}'),
(32, 'DOTUSDT', 'BUY', 0.833333, 3.7976, '2025-06-14 08:38:59', 0, 3.66702, 3.99347, 'multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL, '{\"stop_loss\": 3.6670217514038086, \"take_profit\": 3.9934675693511963, \"migrated_from_columns\": true}'),
(33, 'ETHUSDT', 'SELL', 0.833333, 3444.17, '2025-06-14 08:39:04', 0, 3572.63, 3251.48, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL, '{\"stop_loss\": 3572.63134765625, \"take_profit\": 3251.478271484375, \"migrated_from_columns\": true}'),
(34, 'ADAUSDT', 'BUY', 0.875, 0.71, '2025-06-14 08:39:04', 0, 0.69548, 0.73178, 'multi_indicator', 'RSI: Перепроданность; MACD: Бычье пересечение; Stochastic: Перепроданность + пересечение', NULL, NULL, '{\"stop_loss\": 0.6954801082611084, \"take_profit\": 0.7317798733711243, \"migrated_from_columns\": true}'),
(35, 'DOTUSDT', 'BUY', 0.833333, 3.7976, '2025-06-14 08:39:04', 0, 3.66702, 3.99347, 'multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL, '{\"stop_loss\": 3.6670217514038086, \"take_profit\": 3.9934675693511963, \"migrated_from_columns\": true}'),
(36, 'ETHUSDT', 'SELL', 0.833333, 3444.17, '2025-06-14 08:39:10', 0, 3572.63, 3251.48, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL, '{\"stop_loss\": 3572.63134765625, \"take_profit\": 3251.478271484375, \"migrated_from_columns\": true}'),
(37, 'ADAUSDT', 'BUY', 0.875, 0.71, '2025-06-14 08:39:10', 0, 0.69548, 0.73178, 'multi_indicator', 'RSI: Перепроданность; MACD: Бычье пересечение; Stochastic: Перепроданность + пересечение', NULL, NULL, '{\"stop_loss\": 0.6954801082611084, \"take_profit\": 0.7317798733711243, \"migrated_from_columns\": true}'),
(38, 'DOTUSDT', 'BUY', 0.833333, 3.7976, '2025-06-14 08:39:10', 0, 3.66702, 3.99347, 'multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL, '{\"stop_loss\": 3.6670217514038086, \"take_profit\": 3.9934675693511963, \"migrated_from_columns\": true}'),
(39, 'BNBUSDT', 'BUY', 0.833333, 717, '2025-06-14 13:52:33', 0, 681.15, 788.7, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL, '{\"stop_loss\": 681.1500244140625, \"take_profit\": 788.7000122070312, \"migrated_from_columns\": true}'),
(40, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:53:18', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL, '{\"stop_loss\": 3.515601873397827, \"take_profit\": 3.5665972232818604, \"migrated_from_columns\": true}'),
(41, 'BNBUSDT', 'BUY', 0.833333, 717, '2025-06-14 13:53:24', 0, 681.15, 788.7, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL, '{\"stop_loss\": 681.1500244140625, \"take_profit\": 788.7000122070312, \"migrated_from_columns\": true}'),
(42, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:53:51', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL, '{\"stop_loss\": 3.515601873397827, \"take_profit\": 3.5665972232818604, \"migrated_from_columns\": true}'),
(43, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:54:02', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL, '{\"stop_loss\": 3.515601873397827, \"take_profit\": 3.5665972232818604, \"migrated_from_columns\": true}'),
(44, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:54:04', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL, '{\"stop_loss\": 3.515601873397827, \"take_profit\": 3.5665972232818604, \"migrated_from_columns\": true}'),
(45, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:54:15', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL, '{\"stop_loss\": 3.515601873397827, \"take_profit\": 3.5665972232818604, \"migrated_from_columns\": true}'),
(46, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:54:26', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL, '{\"stop_loss\": 3.515601873397827, \"take_profit\": 3.5665972232818604, \"migrated_from_columns\": true}'),
(47, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:54:32', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL, '{\"stop_loss\": 3.515601873397827, \"take_profit\": 3.5665972232818604, \"migrated_from_columns\": true}'),
(48, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:54:35', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL, '{\"stop_loss\": 3.515601873397827, \"take_profit\": 3.5665972232818604, \"migrated_from_columns\": true}'),
(49, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:54:40', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL, '{\"stop_loss\": 3.515601873397827, \"take_profit\": 3.5665972232818604, \"migrated_from_columns\": true}'),
(50, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:54:46', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL, '{\"stop_loss\": 3.515601873397827, \"take_profit\": 3.5665972232818604, \"migrated_from_columns\": true}'),
(51, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:54:48', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL, '{\"stop_loss\": 3.515601873397827, \"take_profit\": 3.5665972232818604, \"migrated_from_columns\": true}'),
(52, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:54:51', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL, '{\"stop_loss\": 3.515601873397827, \"take_profit\": 3.5665972232818604, \"migrated_from_columns\": true}'),
(53, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:54:57', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL, '{\"stop_loss\": 3.515601873397827, \"take_profit\": 3.5665972232818604, \"migrated_from_columns\": true}'),
(54, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:55:09', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL, '{\"stop_loss\": 3.515601873397827, \"take_profit\": 3.5665972232818604, \"migrated_from_columns\": true}'),
(55, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:55:11', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL, '{\"stop_loss\": 3.515601873397827, \"take_profit\": 3.5665972232818604, \"migrated_from_columns\": true}'),
(56, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:55:21', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL, '{\"stop_loss\": 3.515601873397827, \"take_profit\": 3.5665972232818604, \"migrated_from_columns\": true}'),
(57, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:55:29', 0, 3.51706, 3.56441, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL, '{\"stop_loss\": 3.517058849334717, \"take_profit\": 3.5644118785858154, \"migrated_from_columns\": true}'),
(58, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:55:35', 0, 3.51706, 3.56441, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL, '{\"stop_loss\": 3.517058849334717, \"take_profit\": 3.5644118785858154, \"migrated_from_columns\": true}'),
(59, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:55:38', 0, 3.51706, 3.56441, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL, '{\"stop_loss\": 3.517058849334717, \"take_profit\": 3.5644118785858154, \"migrated_from_columns\": true}'),
(60, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:55:42', 0, 3.51706, 3.56441, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL, '{\"stop_loss\": 3.517058849334717, \"take_profit\": 3.5644118785858154, \"migrated_from_columns\": true}'),
(61, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:55:44', 0, 3.51706, 3.56441, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL, '{\"stop_loss\": 3.517058849334717, \"take_profit\": 3.5644118785858154, \"migrated_from_columns\": true}'),
(62, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:55:49', 0, 3.51706, 3.56441, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL, '{\"stop_loss\": 3.517058849334717, \"take_profit\": 3.5644118785858154, \"migrated_from_columns\": true}'),
(63, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:55:51', 0, 3.51706, 3.56441, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL, '{\"stop_loss\": 3.517058849334717, \"take_profit\": 3.5644118785858154, \"migrated_from_columns\": true}'),
(64, 'BNBUSDT', 'BUY', 0.833333, 710, '2025-06-14 14:01:17', 0, 674.5, 781, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL, '{\"stop_loss\": 674.5, \"take_profit\": 781.0, \"migrated_from_columns\": true}'),
(65, 'XRPUSDT', 'BUY', 0.833333, 3.5392, '2025-06-14 14:01:52', 0, 3.52119, 3.56622, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL, '{\"stop_loss\": 3.5211873054504395, \"take_profit\": 3.5662190914154053, \"migrated_from_columns\": true}'),
(66, 'BNBUSDT', 'BUY', 0.833333, 710, '2025-06-14 14:01:57', 0, 674.5, 781, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL, '{\"stop_loss\": 674.5, \"take_profit\": 781.0, \"migrated_from_columns\": true}'),
(67, 'XRPUSDT', 'BUY', 0.833333, 3.5392, '2025-06-14 14:02:10', 0, 3.52119, 3.56622, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL, '{\"stop_loss\": 3.5211873054504395, \"take_profit\": 3.5662190914154053, \"migrated_from_columns\": true}'),
(68, 'BNBUSDT', 'BUY', 0.833333, 710, '2025-06-14 14:02:23', 0, 674.5, 781, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL, '{\"stop_loss\": 674.5, \"take_profit\": 781.0, \"migrated_from_columns\": true}'),
(69, 'XRPUSDT', 'BUY', 0.833333, 3.5392, '2025-06-14 14:02:40', 0, 3.52119, 3.56622, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL, '{\"stop_loss\": 3.5211873054504395, \"take_profit\": 3.5662190914154053, \"migrated_from_columns\": true}'),
(70, 'BNBUSDT', 'BUY', 0.833333, 710, '2025-06-14 14:02:45', 0, 674.5, 781, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL, '{\"stop_loss\": 674.5, \"take_profit\": 781.0, \"migrated_from_columns\": true}'),
(71, 'BTCUSDT', 'SELL', 0.525, 94666.7, '2025-06-20 13:49:08', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 102453.02899595573, \"market_data\": {\"volatility\": 1.129242258096002, \"volume_24h\": 11789.372, \"price_change_24h\": -8.214982412186986}, \"take_profit\": 82987.20650606639, \"current_price\": 94666.7, \"risk_reward_ratio\": 1.5000000000000018, \"strategy_indicators\": {\"atr\": 3893.164497977868, \"roc\": -7.416249224937364, \"rsi\": 39.302478326187526, \"ema_fast\": 95031.00744022171, \"ema_slow\": 98139.8794940074, \"volume_ratio\": 0.001968141222955449, \"current_price\": 94666.7}}'),
(72, 'ETHUSDT', 'SELL', 0.525, 6897.5, '2025-06-20 13:49:12', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 7082.981799057897, \"market_data\": {\"volatility\": 3.336593768103919, \"volume_24h\": 97.9, \"price_change_24h\": 89.28531244768756}, \"take_profit\": 6619.277301413154, \"current_price\": 6897.5, \"risk_reward_ratio\": 1.5000000000000024, \"strategy_indicators\": {\"atr\": 92.74089952894845, \"roc\": -2.0455752576851083, \"rsi\": 35.467524288638685, \"ema_fast\": 6914.282867779135, \"ema_slow\": 7085.021937096997, \"volume_ratio\": 0.05441037982630534, \"current_price\": 6897.5}}'),
(73, 'BTCUSDT', 'SELL', 0.525, 94666.7, '2025-06-20 13:49:16', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 102453.02899595573, \"market_data\": {\"volatility\": 1.129242258096002, \"volume_24h\": 11789.372, \"price_change_24h\": -8.214982412186986}, \"take_profit\": 82987.20650606639, \"current_price\": 94666.7, \"risk_reward_ratio\": 1.5000000000000018, \"strategy_indicators\": {\"atr\": 3893.164497977868, \"roc\": -7.416249224937364, \"rsi\": 39.302478326187526, \"ema_fast\": 95031.00744022171, \"ema_slow\": 98139.8794940074, \"volume_ratio\": 0.001968141222955449, \"current_price\": 94666.7}}'),
(74, 'ETHUSDT', 'SELL', 0.525, 6897.5, '2025-06-20 13:49:16', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 7082.981799057897, \"market_data\": {\"volatility\": 3.336593768103919, \"volume_24h\": 97.9, \"price_change_24h\": 89.28531244768756}, \"take_profit\": 6619.277301413154, \"current_price\": 6897.5, \"risk_reward_ratio\": 1.5000000000000024, \"strategy_indicators\": {\"atr\": 92.74089952894845, \"roc\": -2.0455752576851083, \"rsi\": 35.467524288638685, \"ema_fast\": 6914.282867779135, \"ema_slow\": 7085.021937096997, \"volume_ratio\": 0.05441037982630534, \"current_price\": 6897.5}}'),
(75, 'BTCUSDT', 'SELL', 0.525, 94666.7, '2025-06-20 13:49:22', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 102453.02899595573, \"market_data\": {\"volatility\": 1.129242258096002, \"volume_24h\": 11789.372, \"price_change_24h\": -8.214982412186986}, \"take_profit\": 82987.20650606639, \"current_price\": 94666.7, \"risk_reward_ratio\": 1.5000000000000018, \"strategy_indicators\": {\"atr\": 3893.164497977868, \"roc\": -7.416249224937364, \"rsi\": 39.302478326187526, \"ema_fast\": 95031.00744022171, \"ema_slow\": 98139.8794940074, \"volume_ratio\": 0.001968141222955449, \"current_price\": 94666.7}}'),
(76, 'ETHUSDT', 'SELL', 0.525, 6897.5, '2025-06-20 13:49:22', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 7082.981799057897, \"market_data\": {\"volatility\": 3.336593768103919, \"volume_24h\": 97.9, \"price_change_24h\": 89.28531244768756}, \"take_profit\": 6619.277301413154, \"current_price\": 6897.5, \"risk_reward_ratio\": 1.5000000000000024, \"strategy_indicators\": {\"atr\": 92.74089952894845, \"roc\": -2.0455752576851083, \"rsi\": 35.467524288638685, \"ema_fast\": 6914.282867779135, \"ema_slow\": 7085.021937096997, \"volume_ratio\": 0.05441037982630534, \"current_price\": 6897.5}}'),
(77, 'BTCUSDT', 'SELL', 0.525, 94666.7, '2025-06-20 13:49:25', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 102453.02899595573, \"market_data\": {\"volatility\": 1.129242258096002, \"volume_24h\": 11789.372, \"price_change_24h\": -8.214982412186986}, \"take_profit\": 82987.20650606639, \"current_price\": 94666.7, \"risk_reward_ratio\": 1.5000000000000018, \"strategy_indicators\": {\"atr\": 3893.164497977868, \"roc\": -7.416249224937364, \"rsi\": 39.302478326187526, \"ema_fast\": 95031.00744022171, \"ema_slow\": 98139.8794940074, \"volume_ratio\": 0.001968141222955449, \"current_price\": 94666.7}}'),
(78, 'ETHUSDT', 'SELL', 0.525, 6897.5, '2025-06-20 13:49:25', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 7082.981799057897, \"market_data\": {\"volatility\": 3.336593768103919, \"volume_24h\": 97.9, \"price_change_24h\": 89.28531244768756}, \"take_profit\": 6619.277301413154, \"current_price\": 6897.5, \"risk_reward_ratio\": 1.5000000000000024, \"strategy_indicators\": {\"atr\": 92.74089952894845, \"roc\": -2.0455752576851083, \"rsi\": 35.467524288638685, \"ema_fast\": 6914.282867779135, \"ema_slow\": 7085.021937096997, \"volume_ratio\": 0.05441037982630534, \"current_price\": 6897.5}}'),
(79, 'BTCUSDT', 'SELL', 0.525, 94666.7, '2025-06-20 13:49:28', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 102453.02899595573, \"market_data\": {\"volatility\": 1.129242258096002, \"volume_24h\": 11789.372, \"price_change_24h\": -8.214982412186986}, \"take_profit\": 82987.20650606639, \"current_price\": 94666.7, \"risk_reward_ratio\": 1.5000000000000018, \"strategy_indicators\": {\"atr\": 3893.164497977868, \"roc\": -7.416249224937364, \"rsi\": 39.302478326187526, \"ema_fast\": 95031.00744022171, \"ema_slow\": 98139.8794940074, \"volume_ratio\": 0.001968141222955449, \"current_price\": 94666.7}}'),
(80, 'ETHUSDT', 'SELL', 0.525, 6897.5, '2025-06-20 13:49:28', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 7082.981799057897, \"market_data\": {\"volatility\": 3.336593768103919, \"volume_24h\": 97.9, \"price_change_24h\": 89.28531244768756}, \"take_profit\": 6619.277301413154, \"current_price\": 6897.5, \"risk_reward_ratio\": 1.5000000000000024, \"strategy_indicators\": {\"atr\": 92.74089952894845, \"roc\": -2.0455752576851083, \"rsi\": 35.467524288638685, \"ema_fast\": 6914.282867779135, \"ema_slow\": 7085.021937096997, \"volume_ratio\": 0.05441037982630534, \"current_price\": 6897.5}}'),
(81, 'BTCUSDT', 'SELL', 0.525, 94666.7, '2025-06-20 13:49:31', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 102453.02899595573, \"market_data\": {\"volatility\": 1.129242258096002, \"volume_24h\": 11789.372, \"price_change_24h\": -8.214982412186986}, \"take_profit\": 82987.20650606639, \"current_price\": 94666.7, \"risk_reward_ratio\": 1.5000000000000018, \"strategy_indicators\": {\"atr\": 3893.164497977868, \"roc\": -7.416249224937364, \"rsi\": 39.302478326187526, \"ema_fast\": 95031.00744022171, \"ema_slow\": 98139.8794940074, \"volume_ratio\": 0.001968141222955449, \"current_price\": 94666.7}}'),
(82, 'ETHUSDT', 'SELL', 0.525, 6897.5, '2025-06-20 13:49:31', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 7082.981799057897, \"market_data\": {\"volatility\": 3.336593768103919, \"volume_24h\": 97.9, \"price_change_24h\": 89.28531244768756}, \"take_profit\": 6619.277301413154, \"current_price\": 6897.5, \"risk_reward_ratio\": 1.5000000000000024, \"strategy_indicators\": {\"atr\": 92.74089952894845, \"roc\": -2.0455752576851083, \"rsi\": 35.467524288638685, \"ema_fast\": 6914.282867779135, \"ema_slow\": 7085.021937096997, \"volume_ratio\": 0.05441037982630534, \"current_price\": 6897.5}}'),
(83, 'BTCUSDT', 'SELL', 0.525, 94666.7, '2025-06-20 13:49:34', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 102453.02899595573, \"market_data\": {\"volatility\": 1.129242258096002, \"volume_24h\": 11789.372, \"price_change_24h\": -8.214982412186986}, \"take_profit\": 82987.20650606639, \"current_price\": 94666.7, \"risk_reward_ratio\": 1.5000000000000018, \"strategy_indicators\": {\"atr\": 3893.164497977868, \"roc\": -7.416249224937364, \"rsi\": 39.302478326187526, \"ema_fast\": 95031.00744022171, \"ema_slow\": 98139.8794940074, \"volume_ratio\": 0.001968141222955449, \"current_price\": 94666.7}}'),
(84, 'ETHUSDT', 'SELL', 0.525, 6897.5, '2025-06-20 13:49:34', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 7082.981799057897, \"market_data\": {\"volatility\": 3.336593768103919, \"volume_24h\": 97.9, \"price_change_24h\": 89.28531244768756}, \"take_profit\": 6619.277301413154, \"current_price\": 6897.5, \"risk_reward_ratio\": 1.5000000000000024, \"strategy_indicators\": {\"atr\": 92.74089952894845, \"roc\": -2.0455752576851083, \"rsi\": 35.467524288638685, \"ema_fast\": 6914.282867779135, \"ema_slow\": 7085.021937096997, \"volume_ratio\": 0.05441037982630534, \"current_price\": 6897.5}}'),
(85, 'BTCUSDT', 'SELL', 0.525, 94666.7, '2025-06-20 13:49:39', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 102453.02899595573, \"market_data\": {\"volatility\": 1.129242258096002, \"volume_24h\": 11789.372, \"price_change_24h\": -8.214982412186986}, \"take_profit\": 82987.20650606639, \"current_price\": 94666.7, \"risk_reward_ratio\": 1.5000000000000018, \"strategy_indicators\": {\"atr\": 3893.164497977868, \"roc\": -7.416249224937364, \"rsi\": 39.302478326187526, \"ema_fast\": 95031.00744022171, \"ema_slow\": 98139.8794940074, \"volume_ratio\": 0.001968141222955449, \"current_price\": 94666.7}}'),
(86, 'ETHUSDT', 'SELL', 0.525, 6897.5, '2025-06-20 13:49:39', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 7082.981799057897, \"market_data\": {\"volatility\": 3.336593768103919, \"volume_24h\": 97.9, \"price_change_24h\": 89.28531244768756}, \"take_profit\": 6619.277301413154, \"current_price\": 6897.5, \"risk_reward_ratio\": 1.5000000000000024, \"strategy_indicators\": {\"atr\": 92.74089952894845, \"roc\": -2.0455752576851083, \"rsi\": 35.467524288638685, \"ema_fast\": 6914.282867779135, \"ema_slow\": 7085.021937096997, \"volume_ratio\": 0.05441037982630534, \"current_price\": 6897.5}}'),
(87, 'BTCUSDT', 'SELL', 0.525, 94666.7, '2025-06-20 13:49:45', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 102453.02899595573, \"market_data\": {\"volatility\": 1.129242258096002, \"volume_24h\": 11789.372, \"price_change_24h\": -8.214982412186986}, \"take_profit\": 82987.20650606639, \"current_price\": 94666.7, \"risk_reward_ratio\": 1.5000000000000018, \"strategy_indicators\": {\"atr\": 3893.164497977868, \"roc\": -7.416249224937364, \"rsi\": 39.302478326187526, \"ema_fast\": 95031.00744022171, \"ema_slow\": 98139.8794940074, \"volume_ratio\": 0.001968141222955449, \"current_price\": 94666.7}}'),
(88, 'ETHUSDT', 'SELL', 0.525, 6897.5, '2025-06-20 13:49:45', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 7082.981799057897, \"market_data\": {\"volatility\": 3.336593768103919, \"volume_24h\": 97.9, \"price_change_24h\": 89.28531244768756}, \"take_profit\": 6619.277301413154, \"current_price\": 6897.5, \"risk_reward_ratio\": 1.5000000000000024, \"strategy_indicators\": {\"atr\": 92.74089952894845, \"roc\": -2.0455752576851083, \"rsi\": 35.467524288638685, \"ema_fast\": 6914.282867779135, \"ema_slow\": 7085.021937096997, \"volume_ratio\": 0.05441037982630534, \"current_price\": 6897.5}}'),
(89, 'BTCUSDT', 'SELL', 0.525, 94666.7, '2025-06-20 13:49:48', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 102453.02899595573, \"market_data\": {\"volatility\": 1.129242258096002, \"volume_24h\": 11789.372, \"price_change_24h\": -8.214982412186986}, \"take_profit\": 82987.20650606639, \"current_price\": 94666.7, \"risk_reward_ratio\": 1.5000000000000018, \"strategy_indicators\": {\"atr\": 3893.164497977868, \"roc\": -7.416249224937364, \"rsi\": 39.302478326187526, \"ema_fast\": 95031.00744022171, \"ema_slow\": 98139.8794940074, \"volume_ratio\": 0.001968141222955449, \"current_price\": 94666.7}}'),
(90, 'ETHUSDT', 'SELL', 0.525, 6897.5, '2025-06-20 13:49:48', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 7082.981799057897, \"market_data\": {\"volatility\": 3.336593768103919, \"volume_24h\": 97.9, \"price_change_24h\": 89.28531244768756}, \"take_profit\": 6619.277301413154, \"current_price\": 6897.5, \"risk_reward_ratio\": 1.5000000000000024, \"strategy_indicators\": {\"atr\": 92.74089952894845, \"roc\": -2.0455752576851083, \"rsi\": 35.467524288638685, \"ema_fast\": 6914.282867779135, \"ema_slow\": 7085.021937096997, \"volume_ratio\": 0.05441037982630534, \"current_price\": 6897.5}}'),
(91, 'BTCUSDT', 'SELL', 0.525, 94666.7, '2025-06-20 13:49:52', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 102453.02899595573, \"market_data\": {\"volatility\": 1.129242258096002, \"volume_24h\": 11789.372, \"price_change_24h\": -8.214982412186986}, \"take_profit\": 82987.20650606639, \"current_price\": 94666.7, \"risk_reward_ratio\": 1.5000000000000018, \"strategy_indicators\": {\"atr\": 3893.164497977868, \"roc\": -7.416249224937364, \"rsi\": 39.302478326187526, \"ema_fast\": 95031.00744022171, \"ema_slow\": 98139.8794940074, \"volume_ratio\": 0.001968141222955449, \"current_price\": 94666.7}}'),
(92, 'ETHUSDT', 'SELL', 0.525, 6897.5, '2025-06-20 13:49:52', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 7082.981799057897, \"market_data\": {\"volatility\": 3.336593768103919, \"volume_24h\": 97.9, \"price_change_24h\": 89.28531244768756}, \"take_profit\": 6619.277301413154, \"current_price\": 6897.5, \"risk_reward_ratio\": 1.5000000000000024, \"strategy_indicators\": {\"atr\": 92.74089952894845, \"roc\": -2.0455752576851083, \"rsi\": 35.467524288638685, \"ema_fast\": 6914.282867779135, \"ema_slow\": 7085.021937096997, \"volume_ratio\": 0.05441037982630534, \"current_price\": 6897.5}}'),
(93, 'BTCUSDT', 'SELL', 0.525, 94666.7, '2025-06-20 13:49:57', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 102453.02899595573, \"market_data\": {\"volatility\": 1.129242258096002, \"volume_24h\": 11789.372, \"price_change_24h\": -8.214982412186986}, \"take_profit\": 82987.20650606639, \"current_price\": 94666.7, \"risk_reward_ratio\": 1.5000000000000018, \"strategy_indicators\": {\"atr\": 3893.164497977868, \"roc\": -7.416249224937364, \"rsi\": 39.302478326187526, \"ema_fast\": 95031.00744022171, \"ema_slow\": 98139.8794940074, \"volume_ratio\": 0.001968141222955449, \"current_price\": 94666.7}}'),
(94, 'ETHUSDT', 'SELL', 0.525, 6897.5, '2025-06-20 13:49:57', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 7082.981799057897, \"market_data\": {\"volatility\": 3.336593768103919, \"volume_24h\": 97.9, \"price_change_24h\": 89.28531244768756}, \"take_profit\": 6619.277301413154, \"current_price\": 6897.5, \"risk_reward_ratio\": 1.5000000000000024, \"strategy_indicators\": {\"atr\": 92.74089952894845, \"roc\": -2.0455752576851083, \"rsi\": 35.467524288638685, \"ema_fast\": 6914.282867779135, \"ema_slow\": 7085.021937096997, \"volume_ratio\": 0.05441037982630534, \"current_price\": 6897.5}}'),
(95, 'BTCUSDT', 'SELL', 0.525, 94666.7, '2025-06-20 13:50:01', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 102453.02899595573, \"market_data\": {\"volatility\": 1.129242258096002, \"volume_24h\": 11789.372, \"price_change_24h\": -8.214982412186986}, \"take_profit\": 82987.20650606639, \"current_price\": 94666.7, \"risk_reward_ratio\": 1.5000000000000018, \"strategy_indicators\": {\"atr\": 3893.164497977868, \"roc\": -7.416249224937364, \"rsi\": 39.302478326187526, \"ema_fast\": 95031.00744022171, \"ema_slow\": 98139.8794940074, \"volume_ratio\": 0.001968141222955449, \"current_price\": 94666.7}}'),
(96, 'ETHUSDT', 'SELL', 0.525, 6897.5, '2025-06-20 13:50:01', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 7082.981799057897, \"market_data\": {\"volatility\": 3.336593768103919, \"volume_24h\": 97.9, \"price_change_24h\": 89.28531244768756}, \"take_profit\": 6619.277301413154, \"current_price\": 6897.5, \"risk_reward_ratio\": 1.5000000000000024, \"strategy_indicators\": {\"atr\": 92.74089952894845, \"roc\": -2.0455752576851083, \"rsi\": 35.467524288638685, \"ema_fast\": 6914.282867779135, \"ema_slow\": 7085.021937096997, \"volume_ratio\": 0.05441037982630534, \"current_price\": 6897.5}}'),
(97, 'BTCUSDT', 'SELL', 0.525, 94666.7, '2025-06-20 13:50:06', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 102453.02899595573, \"market_data\": {\"volatility\": 1.129242258096002, \"volume_24h\": 11789.372, \"price_change_24h\": -8.214982412186986}, \"take_profit\": 82987.20650606639, \"current_price\": 94666.7, \"risk_reward_ratio\": 1.5000000000000018, \"strategy_indicators\": {\"atr\": 3893.164497977868, \"roc\": -7.416249224937364, \"rsi\": 39.302478326187526, \"ema_fast\": 95031.00744022171, \"ema_slow\": 98139.8794940074, \"volume_ratio\": 0.001968141222955449, \"current_price\": 94666.7}}'),
(98, 'ETHUSDT', 'SELL', 0.525, 6897.5, '2025-06-20 13:50:06', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 7082.981799057897, \"market_data\": {\"volatility\": 3.336593768103919, \"volume_24h\": 97.9, \"price_change_24h\": 89.28531244768756}, \"take_profit\": 6619.277301413154, \"current_price\": 6897.5, \"risk_reward_ratio\": 1.5000000000000024, \"strategy_indicators\": {\"atr\": 92.74089952894845, \"roc\": -2.0455752576851083, \"rsi\": 35.467524288638685, \"ema_fast\": 6914.282867779135, \"ema_slow\": 7085.021937096997, \"volume_ratio\": 0.05441037982630534, \"current_price\": 6897.5}}'),
(99, 'BTCUSDT', 'SELL', 0.525, 94533.4, '2025-06-20 13:50:12', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 101782.60548889686, \"market_data\": {\"volatility\": 1.129186669442729, \"volume_24h\": 11788.989, \"price_change_24h\": -8.137055788235987}, \"take_profit\": 83659.59176665469, \"current_price\": 94533.4, \"risk_reward_ratio\": 1.5, \"strategy_indicators\": {\"atr\": 3624.6027444484366, \"roc\": -4.264157822247434, \"rsi\": 39.057270197070466, \"ema_fast\": 94931.48595217738, \"ema_slow\": 97812.0177206001, \"volume_ratio\": 0.000003393371405263815, \"current_price\": 94533.4}}'),
(100, 'ETHUSDT', 'SELL', 0.525, 6897.5, '2025-06-20 13:50:12', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 7082.981799057897, \"market_data\": {\"volatility\": 3.336593768103919, \"volume_24h\": 97.9, \"price_change_24h\": 89.28531244768756}, \"take_profit\": 6619.277301413154, \"current_price\": 6897.5, \"risk_reward_ratio\": 1.5000000000000024, \"strategy_indicators\": {\"atr\": 92.74089952894845, \"roc\": -2.0455752576851083, \"rsi\": 35.467524288638685, \"ema_fast\": 6914.282867779135, \"ema_slow\": 7085.021937096997, \"volume_ratio\": 0.05441037982630534, \"current_price\": 6897.5}}'),
(101, 'BTCUSDT', 'SELL', 0.525, 94533.4, '2025-06-20 13:50:13', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 101782.60548889686, \"market_data\": {\"volatility\": 1.129186669442729, \"volume_24h\": 11788.989, \"price_change_24h\": -8.137055788235987}, \"take_profit\": 83659.59176665469, \"current_price\": 94533.4, \"risk_reward_ratio\": 1.5, \"strategy_indicators\": {\"atr\": 3624.6027444484366, \"roc\": -4.264157822247434, \"rsi\": 39.057270197070466, \"ema_fast\": 94931.48595217738, \"ema_slow\": 97812.0177206001, \"volume_ratio\": 0.000003393371405263815, \"current_price\": 94533.4}}'),
(102, 'BTCUSDT', 'SELL', 0.525, 94533.4, '2025-06-20 13:50:21', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 101782.60548889686, \"market_data\": {\"volatility\": 1.129186669442729, \"volume_24h\": 11788.989, \"price_change_24h\": -8.137055788235987}, \"take_profit\": 83659.59176665469, \"current_price\": 94533.4, \"risk_reward_ratio\": 1.5, \"strategy_indicators\": {\"atr\": 3624.6027444484366, \"roc\": -4.264157822247434, \"rsi\": 39.057270197070466, \"ema_fast\": 94931.48595217738, \"ema_slow\": 97812.0177206001, \"volume_ratio\": 0.000003393371405263815, \"current_price\": 94533.4}}'),
(103, 'BTCUSDT', 'SELL', 0.525, 94533.4, '2025-06-20 13:50:25', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 101782.60548889686, \"market_data\": {\"volatility\": 1.129186669442729, \"volume_24h\": 11788.989, \"price_change_24h\": -8.137055788235987}, \"take_profit\": 83659.59176665469, \"current_price\": 94533.4, \"risk_reward_ratio\": 1.5, \"strategy_indicators\": {\"atr\": 3624.6027444484366, \"roc\": -4.264157822247434, \"rsi\": 39.057270197070466, \"ema_fast\": 94931.48595217738, \"ema_slow\": 97812.0177206001, \"volume_ratio\": 0.000003393371405263815, \"current_price\": 94533.4}}'),
(104, 'BTCUSDT', 'SELL', 0.525, 94533.4, '2025-06-20 13:50:30', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 101782.60548889686, \"market_data\": {\"volatility\": 1.129186669442729, \"volume_24h\": 11788.989, \"price_change_24h\": -8.137055788235987}, \"take_profit\": 83659.59176665469, \"current_price\": 94533.4, \"risk_reward_ratio\": 1.5, \"strategy_indicators\": {\"atr\": 3624.6027444484366, \"roc\": -4.264157822247434, \"rsi\": 39.057270197070466, \"ema_fast\": 94931.48595217738, \"ema_slow\": 97812.0177206001, \"volume_ratio\": 0.000003393371405263815, \"current_price\": 94533.4}}'),
(105, 'BTCUSDT', 'SELL', 0.525, 94533.4, '2025-06-20 13:50:32', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 101782.60548889686, \"market_data\": {\"volatility\": 1.129186669442729, \"volume_24h\": 11788.989, \"price_change_24h\": -8.137055788235987}, \"take_profit\": 83659.59176665469, \"current_price\": 94533.4, \"risk_reward_ratio\": 1.5, \"strategy_indicators\": {\"atr\": 3624.6027444484366, \"roc\": -4.264157822247434, \"rsi\": 39.057270197070466, \"ema_fast\": 94931.48595217738, \"ema_slow\": 97812.0177206001, \"volume_ratio\": 0.000003393371405263815, \"current_price\": 94533.4}}'),
(106, 'BTCUSDT', 'SELL', 0.525, 94533.4, '2025-06-20 13:50:35', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 101782.60548889686, \"market_data\": {\"volatility\": 1.129186669442729, \"volume_24h\": 11788.989, \"price_change_24h\": -8.137055788235987}, \"take_profit\": 83659.59176665469, \"current_price\": 94533.4, \"risk_reward_ratio\": 1.5, \"strategy_indicators\": {\"atr\": 3624.6027444484366, \"roc\": -4.264157822247434, \"rsi\": 39.057270197070466, \"ema_fast\": 94931.48595217738, \"ema_slow\": 97812.0177206001, \"volume_ratio\": 0.000003393371405263815, \"current_price\": 94533.4}}'),
(107, 'BTCUSDT', 'SELL', 0.525, 94533.4, '2025-06-20 13:50:40', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 101782.60548889686, \"market_data\": {\"volatility\": 1.129186669442729, \"volume_24h\": 11788.989, \"price_change_24h\": -8.137055788235987}, \"take_profit\": 83659.59176665469, \"current_price\": 94533.4, \"risk_reward_ratio\": 1.5, \"strategy_indicators\": {\"atr\": 3624.6027444484366, \"roc\": -4.264157822247434, \"rsi\": 39.057270197070466, \"ema_fast\": 94931.48595217738, \"ema_slow\": 97812.0177206001, \"volume_ratio\": 0.000003393371405263815, \"current_price\": 94533.4}}'),
(108, 'BTCUSDT', 'SELL', 0.525, 94533.4, '2025-06-20 13:50:43', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 101782.60548889686, \"market_data\": {\"volatility\": 1.129186669442729, \"volume_24h\": 11788.989, \"price_change_24h\": -8.137055788235987}, \"take_profit\": 83659.59176665469, \"current_price\": 94533.4, \"risk_reward_ratio\": 1.5, \"strategy_indicators\": {\"atr\": 3624.6027444484366, \"roc\": -4.264157822247434, \"rsi\": 39.057270197070466, \"ema_fast\": 94931.48595217738, \"ema_slow\": 97812.0177206001, \"volume_ratio\": 0.000003393371405263815, \"current_price\": 94533.4}}'),
(109, 'BTCUSDT', 'SELL', 0.525, 94533.4, '2025-06-20 13:50:47', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 101782.60548889686, \"market_data\": {\"volatility\": 1.129186669442729, \"volume_24h\": 11788.989, \"price_change_24h\": -8.137055788235987}, \"take_profit\": 83659.59176665469, \"current_price\": 94533.4, \"risk_reward_ratio\": 1.5, \"strategy_indicators\": {\"atr\": 3624.6027444484366, \"roc\": -4.264157822247434, \"rsi\": 39.057270197070466, \"ema_fast\": 94931.48595217738, \"ema_slow\": 97812.0177206001, \"volume_ratio\": 0.000003393371405263815, \"current_price\": 94533.4}}'),
(110, 'BTCUSDT', 'SELL', 0.525, 94533.4, '2025-06-20 13:50:52', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 101782.60548889686, \"market_data\": {\"volatility\": 1.129186669442729, \"volume_24h\": 11788.989, \"price_change_24h\": -8.137055788235987}, \"take_profit\": 83659.59176665469, \"current_price\": 94533.4, \"risk_reward_ratio\": 1.5, \"strategy_indicators\": {\"atr\": 3624.6027444484366, \"roc\": -4.264157822247434, \"rsi\": 39.057270197070466, \"ema_fast\": 94931.48595217738, \"ema_slow\": 97812.0177206001, \"volume_ratio\": 0.000003393371405263815, \"current_price\": 94533.4}}'),
(111, 'BTCUSDT', 'SELL', 0.525, 94533.4, '2025-06-20 13:50:57', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 101782.60548889686, \"market_data\": {\"volatility\": 1.129186669442729, \"volume_24h\": 11788.989, \"price_change_24h\": -8.137055788235987}, \"take_profit\": 83659.59176665469, \"current_price\": 94533.4, \"risk_reward_ratio\": 1.5, \"strategy_indicators\": {\"atr\": 3624.6027444484366, \"roc\": -4.264157822247434, \"rsi\": 39.057270197070466, \"ema_fast\": 94931.48595217738, \"ema_slow\": 97812.0177206001, \"volume_ratio\": 0.000003393371405263815, \"current_price\": 94533.4}}'),
(112, 'BTCUSDT', 'SELL', 0.525, 94533.4, '2025-06-20 13:51:01', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 101782.60548889686, \"market_data\": {\"volatility\": 1.129186669442729, \"volume_24h\": 11788.989, \"price_change_24h\": -8.137055788235987}, \"take_profit\": 83659.59176665469, \"current_price\": 94533.4, \"risk_reward_ratio\": 1.5, \"strategy_indicators\": {\"atr\": 3624.6027444484366, \"roc\": -4.264157822247434, \"rsi\": 39.057270197070466, \"ema_fast\": 94931.48595217738, \"ema_slow\": 97812.0177206001, \"volume_ratio\": 0.000003393371405263815, \"current_price\": 94533.4}}');
INSERT INTO `signals` (`id`, `symbol`, `action`, `confidence`, `price`, `created_at`, `is_executed`, `stop_loss`, `take_profit`, `strategy`, `reason`, `executed_at`, `trade_id`, `indicators`) VALUES
(113, 'BTCUSDT', 'SELL', 0.525, 94533.4, '2025-06-20 13:51:05', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 101782.60548889686, \"market_data\": {\"volatility\": 1.129186669442729, \"volume_24h\": 11788.989, \"price_change_24h\": -8.137055788235987}, \"take_profit\": 83659.59176665469, \"current_price\": 94533.4, \"risk_reward_ratio\": 1.5, \"strategy_indicators\": {\"atr\": 3624.6027444484366, \"roc\": -4.264157822247434, \"rsi\": 39.057270197070466, \"ema_fast\": 94931.48595217738, \"ema_slow\": 97812.0177206001, \"volume_ratio\": 0.000003393371405263815, \"current_price\": 94533.4}}'),
(114, 'BTCUSDT', 'SELL', 0.525, 94533.4, '2025-06-20 13:51:09', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 101782.60548889686, \"market_data\": {\"volatility\": 1.129186669442729, \"volume_24h\": 11788.989, \"price_change_24h\": -8.137055788235987}, \"take_profit\": 83659.59176665469, \"current_price\": 94533.4, \"risk_reward_ratio\": 1.5, \"strategy_indicators\": {\"atr\": 3624.6027444484366, \"roc\": -4.264157822247434, \"rsi\": 39.057270197070466, \"ema_fast\": 94931.48595217738, \"ema_slow\": 97812.0177206001, \"volume_ratio\": 0.000003393371405263815, \"current_price\": 94533.4}}'),
(115, 'BTCUSDT', 'SELL', 0.525, 94533.4, '2025-06-20 13:51:12', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 101782.60548889686, \"market_data\": {\"volatility\": 1.129186669442729, \"volume_24h\": 11788.989, \"price_change_24h\": -8.137055788235987}, \"take_profit\": 83659.59176665469, \"current_price\": 94533.4, \"risk_reward_ratio\": 1.5, \"strategy_indicators\": {\"atr\": 3624.6027444484366, \"roc\": -4.264157822247434, \"rsi\": 39.057270197070466, \"ema_fast\": 94931.48595217738, \"ema_slow\": 97812.0177206001, \"volume_ratio\": 0.000003393371405263815, \"current_price\": 94533.4}}'),
(116, 'BTCUSDT', 'SELL', 0.525, 94878.1, '2025-06-20 13:51:18', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 102190.3912031826, \"market_data\": {\"volatility\": 1.1293113564457078, \"volume_24h\": 11789.052, \"price_change_24h\": -7.802093152069338}, \"take_profit\": 83909.66319522612, \"current_price\": 94878.1, \"risk_reward_ratio\": 1.5000000000000009, \"strategy_indicators\": {\"atr\": 3656.1456015912945, \"roc\": -3.915073320910631, \"rsi\": 39.90085755484824, \"ema_fast\": 95000.42595217738, \"ema_slow\": 97843.35408423646, \"volume_ratio\": 0.0001102839812517232, \"current_price\": 94878.1}}'),
(117, 'BTCUSDT', 'SELL', 0.525, 94878.1, '2025-06-20 13:51:26', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 102190.3912031826, \"market_data\": {\"volatility\": 1.1293113564457078, \"volume_24h\": 11789.052, \"price_change_24h\": -7.802093152069338}, \"take_profit\": 83909.66319522612, \"current_price\": 94878.1, \"risk_reward_ratio\": 1.5000000000000009, \"strategy_indicators\": {\"atr\": 3656.1456015912945, \"roc\": -3.915073320910631, \"rsi\": 39.90085755484824, \"ema_fast\": 95000.42595217738, \"ema_slow\": 97843.35408423646, \"volume_ratio\": 0.0001102839812517232, \"current_price\": 94878.1}}'),
(118, 'BTCUSDT', 'SELL', 0.525, 94878.1, '2025-06-20 13:51:29', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 102190.3912031826, \"market_data\": {\"volatility\": 1.1293113564457078, \"volume_24h\": 11789.052, \"price_change_24h\": -7.802093152069338}, \"take_profit\": 83909.66319522612, \"current_price\": 94878.1, \"risk_reward_ratio\": 1.5000000000000009, \"strategy_indicators\": {\"atr\": 3656.1456015912945, \"roc\": -3.915073320910631, \"rsi\": 39.90085755484824, \"ema_fast\": 95000.42595217738, \"ema_slow\": 97843.35408423646, \"volume_ratio\": 0.0001102839812517232, \"current_price\": 94878.1}}'),
(119, 'BTCUSDT', 'SELL', 0.525, 94878.1, '2025-06-20 13:51:34', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 102190.3912031826, \"market_data\": {\"volatility\": 1.1293113564457078, \"volume_24h\": 11789.052, \"price_change_24h\": -7.802093152069338}, \"take_profit\": 83909.66319522612, \"current_price\": 94878.1, \"risk_reward_ratio\": 1.5000000000000009, \"strategy_indicators\": {\"atr\": 3656.1456015912945, \"roc\": -3.915073320910631, \"rsi\": 39.90085755484824, \"ema_fast\": 95000.42595217738, \"ema_slow\": 97843.35408423646, \"volume_ratio\": 0.0001102839812517232, \"current_price\": 94878.1}}'),
(120, 'BTCUSDT', 'SELL', 0.525, 94878.1, '2025-06-20 13:51:37', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 102190.3912031826, \"market_data\": {\"volatility\": 1.1293113564457078, \"volume_24h\": 11789.052, \"price_change_24h\": -7.802093152069338}, \"take_profit\": 83909.66319522612, \"current_price\": 94878.1, \"risk_reward_ratio\": 1.5000000000000009, \"strategy_indicators\": {\"atr\": 3656.1456015912945, \"roc\": -3.915073320910631, \"rsi\": 39.90085755484824, \"ema_fast\": 95000.42595217738, \"ema_slow\": 97843.35408423646, \"volume_ratio\": 0.0001102839812517232, \"current_price\": 94878.1}}'),
(121, 'BTCUSDT', 'SELL', 0.525, 94878.1, '2025-06-20 13:51:40', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 102190.3912031826, \"market_data\": {\"volatility\": 1.1293113564457078, \"volume_24h\": 11789.052, \"price_change_24h\": -7.802093152069338}, \"take_profit\": 83909.66319522612, \"current_price\": 94878.1, \"risk_reward_ratio\": 1.5000000000000009, \"strategy_indicators\": {\"atr\": 3656.1456015912945, \"roc\": -3.915073320910631, \"rsi\": 39.90085755484824, \"ema_fast\": 95000.42595217738, \"ema_slow\": 97843.35408423646, \"volume_ratio\": 0.0001102839812517232, \"current_price\": 94878.1}}'),
(122, 'BTCUSDT', 'SELL', 0.525, 94878.1, '2025-06-20 13:51:44', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 102190.3912031826, \"market_data\": {\"volatility\": 1.1293113564457078, \"volume_24h\": 11789.052, \"price_change_24h\": -7.802093152069338}, \"take_profit\": 83909.66319522612, \"current_price\": 94878.1, \"risk_reward_ratio\": 1.5000000000000009, \"strategy_indicators\": {\"atr\": 3656.1456015912945, \"roc\": -3.915073320910631, \"rsi\": 39.90085755484824, \"ema_fast\": 95000.42595217738, \"ema_slow\": 97843.35408423646, \"volume_ratio\": 0.0001102839812517232, \"current_price\": 94878.1}}'),
(123, 'BTCUSDT', 'SELL', 0.525, 94878.1, '2025-06-20 13:51:49', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 102190.3912031826, \"market_data\": {\"volatility\": 1.1293113564457078, \"volume_24h\": 11789.052, \"price_change_24h\": -7.802093152069338}, \"take_profit\": 83909.66319522612, \"current_price\": 94878.1, \"risk_reward_ratio\": 1.5000000000000009, \"strategy_indicators\": {\"atr\": 3656.1456015912945, \"roc\": -3.915073320910631, \"rsi\": 39.90085755484824, \"ema_fast\": 95000.42595217738, \"ema_slow\": 97843.35408423646, \"volume_ratio\": 0.0001102839812517232, \"current_price\": 94878.1}}'),
(124, 'BTCUSDT', 'SELL', 0.525, 94878.1, '2025-06-20 13:51:53', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 102190.3912031826, \"market_data\": {\"volatility\": 1.1293113564457078, \"volume_24h\": 11789.052, \"price_change_24h\": -7.802093152069338}, \"take_profit\": 83909.66319522612, \"current_price\": 94878.1, \"risk_reward_ratio\": 1.5000000000000009, \"strategy_indicators\": {\"atr\": 3656.1456015912945, \"roc\": -3.915073320910631, \"rsi\": 39.90085755484824, \"ema_fast\": 95000.42595217738, \"ema_slow\": 97843.35408423646, \"volume_ratio\": 0.0001102839812517232, \"current_price\": 94878.1}}'),
(125, 'BTCUSDT', 'SELL', 0.525, 94878.1, '2025-06-20 13:51:58', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 102190.3912031826, \"market_data\": {\"volatility\": 1.1293113564457078, \"volume_24h\": 11789.052, \"price_change_24h\": -7.802093152069338}, \"take_profit\": 83909.66319522612, \"current_price\": 94878.1, \"risk_reward_ratio\": 1.5000000000000009, \"strategy_indicators\": {\"atr\": 3656.1456015912945, \"roc\": -3.915073320910631, \"rsi\": 39.90085755484824, \"ema_fast\": 95000.42595217738, \"ema_slow\": 97843.35408423646, \"volume_ratio\": 0.0001102839812517232, \"current_price\": 94878.1}}'),
(126, 'BTCUSDT', 'SELL', 0.525, 94878.1, '2025-06-20 13:52:02', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 102190.3912031826, \"market_data\": {\"volatility\": 1.1293113564457078, \"volume_24h\": 11789.052, \"price_change_24h\": -7.802093152069338}, \"take_profit\": 83909.66319522612, \"current_price\": 94878.1, \"risk_reward_ratio\": 1.5000000000000009, \"strategy_indicators\": {\"atr\": 3656.1456015912945, \"roc\": -3.915073320910631, \"rsi\": 39.90085755484824, \"ema_fast\": 95000.42595217738, \"ema_slow\": 97843.35408423646, \"volume_ratio\": 0.0001102839812517232, \"current_price\": 94878.1}}'),
(127, 'BTCUSDT', 'SELL', 0.525, 94878.1, '2025-06-20 13:52:05', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 102190.3912031826, \"market_data\": {\"volatility\": 1.1293113564457078, \"volume_24h\": 11789.052, \"price_change_24h\": -7.802093152069338}, \"take_profit\": 83909.66319522612, \"current_price\": 94878.1, \"risk_reward_ratio\": 1.5000000000000009, \"strategy_indicators\": {\"atr\": 3656.1456015912945, \"roc\": -3.915073320910631, \"rsi\": 39.90085755484824, \"ema_fast\": 95000.42595217738, \"ema_slow\": 97843.35408423646, \"volume_ratio\": 0.0001102839812517232, \"current_price\": 94878.1}}'),
(128, 'BTCUSDT', 'SELL', 0.525, 94878.1, '2025-06-20 13:52:11', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 102190.3912031826, \"market_data\": {\"volatility\": 1.1293113564457078, \"volume_24h\": 11789.052, \"price_change_24h\": -7.802093152069338}, \"take_profit\": 83909.66319522612, \"current_price\": 94878.1, \"risk_reward_ratio\": 1.5000000000000009, \"strategy_indicators\": {\"atr\": 3656.1456015912945, \"roc\": -3.915073320910631, \"rsi\": 39.90085755484824, \"ema_fast\": 95000.42595217738, \"ema_slow\": 97843.35408423646, \"volume_ratio\": 0.0001102839812517232, \"current_price\": 94878.1}}'),
(129, 'BTCUSDT', 'SELL', 0.525, 94878.1, '2025-06-20 13:52:13', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 102190.3912031826, \"market_data\": {\"volatility\": 1.1293113564457078, \"volume_24h\": 11789.052, \"price_change_24h\": -7.802093152069338}, \"take_profit\": 83909.66319522612, \"current_price\": 94878.1, \"risk_reward_ratio\": 1.5000000000000009, \"strategy_indicators\": {\"atr\": 3656.1456015912945, \"roc\": -3.915073320910631, \"rsi\": 39.90085755484824, \"ema_fast\": 95000.42595217738, \"ema_slow\": 97843.35408423646, \"volume_ratio\": 0.0001102839812517232, \"current_price\": 94878.1}}'),
(130, 'BTCUSDT', 'SELL', 0.525, 94878.1, '2025-06-20 13:52:17', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 102190.3912031826, \"market_data\": {\"volatility\": 1.1293113564457078, \"volume_24h\": 11789.052, \"price_change_24h\": -7.802093152069338}, \"take_profit\": 83909.66319522612, \"current_price\": 94878.1, \"risk_reward_ratio\": 1.5000000000000009, \"strategy_indicators\": {\"atr\": 3656.1456015912945, \"roc\": -3.915073320910631, \"rsi\": 39.90085755484824, \"ema_fast\": 95000.42595217738, \"ema_slow\": 97843.35408423646, \"volume_ratio\": 0.0001102839812517232, \"current_price\": 94878.1}}'),
(131, 'BTCUSDT', 'SELL', 0.525, 94666.7, '2025-06-20 13:52:25', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 101978.99120318258, \"market_data\": {\"volatility\": 1.1291649232183454, \"volume_24h\": 11789.113, \"price_change_24h\": -8.007521354232464}, \"take_profit\": 83698.26319522611, \"current_price\": 94666.7, \"risk_reward_ratio\": 1.5000000000000009, \"strategy_indicators\": {\"atr\": 3656.1456015912945, \"roc\": -4.129162278214375, \"rsi\": 39.30247849573088, \"ema_fast\": 94958.14595217736, \"ema_slow\": 97824.13590241827, \"volume_ratio\": 0.0002137801496817349, \"current_price\": 94666.7}}'),
(132, 'BTCUSDT', 'SELL', 0.525, 94666.7, '2025-06-20 13:52:31', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 101978.99120318258, \"market_data\": {\"volatility\": 1.1291649232183454, \"volume_24h\": 11789.113, \"price_change_24h\": -8.007521354232464}, \"take_profit\": 83698.26319522611, \"current_price\": 94666.7, \"risk_reward_ratio\": 1.5000000000000009, \"strategy_indicators\": {\"atr\": 3656.1456015912945, \"roc\": -4.129162278214375, \"rsi\": 39.30247849573088, \"ema_fast\": 94958.14595217736, \"ema_slow\": 97824.13590241827, \"volume_ratio\": 0.0002137801496817349, \"current_price\": 94666.7}}'),
(133, 'BTCUSDT', 'SELL', 0.525, 94666.7, '2025-06-20 13:52:35', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 101978.99120318258, \"market_data\": {\"volatility\": 1.1291649232183454, \"volume_24h\": 11789.113, \"price_change_24h\": -8.007521354232464}, \"take_profit\": 83698.26319522611, \"current_price\": 94666.7, \"risk_reward_ratio\": 1.5000000000000009, \"strategy_indicators\": {\"atr\": 3656.1456015912945, \"roc\": -4.129162278214375, \"rsi\": 39.30247849573088, \"ema_fast\": 94958.14595217736, \"ema_slow\": 97824.13590241827, \"volume_ratio\": 0.0002137801496817349, \"current_price\": 94666.7}}'),
(134, 'BTCUSDT', 'SELL', 0.525, 94666.7, '2025-06-20 13:52:39', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 101978.99120318258, \"market_data\": {\"volatility\": 1.1291649232183454, \"volume_24h\": 11789.113, \"price_change_24h\": -8.007521354232464}, \"take_profit\": 83698.26319522611, \"current_price\": 94666.7, \"risk_reward_ratio\": 1.5000000000000009, \"strategy_indicators\": {\"atr\": 3656.1456015912945, \"roc\": -4.129162278214375, \"rsi\": 39.30247849573088, \"ema_fast\": 94958.14595217736, \"ema_slow\": 97824.13590241827, \"volume_ratio\": 0.0002137801496817349, \"current_price\": 94666.7}}'),
(135, 'BTCUSDT', 'SELL', 0.525, 94666.7, '2025-06-20 13:52:43', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 101978.99120318258, \"market_data\": {\"volatility\": 1.1291649232183454, \"volume_24h\": 11789.113, \"price_change_24h\": -8.007521354232464}, \"take_profit\": 83698.26319522611, \"current_price\": 94666.7, \"risk_reward_ratio\": 1.5000000000000009, \"strategy_indicators\": {\"atr\": 3656.1456015912945, \"roc\": -4.129162278214375, \"rsi\": 39.30247849573088, \"ema_fast\": 94958.14595217736, \"ema_slow\": 97824.13590241827, \"volume_ratio\": 0.0002137801496817349, \"current_price\": 94666.7}}'),
(136, 'BTCUSDT', 'SELL', 0.525, 94666.7, '2025-06-20 13:52:46', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 101978.99120318258, \"market_data\": {\"volatility\": 1.1291649232183454, \"volume_24h\": 11789.113, \"price_change_24h\": -8.007521354232464}, \"take_profit\": 83698.26319522611, \"current_price\": 94666.7, \"risk_reward_ratio\": 1.5000000000000009, \"strategy_indicators\": {\"atr\": 3656.1456015912945, \"roc\": -4.129162278214375, \"rsi\": 39.30247849573088, \"ema_fast\": 94958.14595217736, \"ema_slow\": 97824.13590241827, \"volume_ratio\": 0.0002137801496817349, \"current_price\": 94666.7}}'),
(137, 'BTCUSDT', 'SELL', 0.525, 94666.7, '2025-06-20 13:52:48', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 101978.99120318258, \"market_data\": {\"volatility\": 1.1291649232183454, \"volume_24h\": 11789.113, \"price_change_24h\": -8.007521354232464}, \"take_profit\": 83698.26319522611, \"current_price\": 94666.7, \"risk_reward_ratio\": 1.5000000000000009, \"strategy_indicators\": {\"atr\": 3656.1456015912945, \"roc\": -4.129162278214375, \"rsi\": 39.30247849573088, \"ema_fast\": 94958.14595217736, \"ema_slow\": 97824.13590241827, \"volume_ratio\": 0.0002137801496817349, \"current_price\": 94666.7}}'),
(138, 'BTCUSDT', 'SELL', 0.525, 94666.7, '2025-06-20 13:52:52', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 101978.99120318258, \"market_data\": {\"volatility\": 1.1291649232183454, \"volume_24h\": 11789.113, \"price_change_24h\": -8.007521354232464}, \"take_profit\": 83698.26319522611, \"current_price\": 94666.7, \"risk_reward_ratio\": 1.5000000000000009, \"strategy_indicators\": {\"atr\": 3656.1456015912945, \"roc\": -4.129162278214375, \"rsi\": 39.30247849573088, \"ema_fast\": 94958.14595217736, \"ema_slow\": 97824.13590241827, \"volume_ratio\": 0.0002137801496817349, \"current_price\": 94666.7}}'),
(139, 'BTCUSDT', 'SELL', 0.525, 94666.7, '2025-06-20 13:52:57', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 101978.99120318258, \"market_data\": {\"volatility\": 1.1291649232183454, \"volume_24h\": 11789.113, \"price_change_24h\": -8.007521354232464}, \"take_profit\": 83698.26319522611, \"current_price\": 94666.7, \"risk_reward_ratio\": 1.5000000000000009, \"strategy_indicators\": {\"atr\": 3656.1456015912945, \"roc\": -4.129162278214375, \"rsi\": 39.30247849573088, \"ema_fast\": 94958.14595217736, \"ema_slow\": 97824.13590241827, \"volume_ratio\": 0.0002137801496817349, \"current_price\": 94666.7}}'),
(140, 'BTCUSDT', 'SELL', 0.525, 94666.7, '2025-06-20 13:53:02', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 101978.99120318258, \"market_data\": {\"volatility\": 1.1291649232183454, \"volume_24h\": 11789.113, \"price_change_24h\": -8.007521354232464}, \"take_profit\": 83698.26319522611, \"current_price\": 94666.7, \"risk_reward_ratio\": 1.5000000000000009, \"strategy_indicators\": {\"atr\": 3656.1456015912945, \"roc\": -4.129162278214375, \"rsi\": 39.30247849573088, \"ema_fast\": 94958.14595217736, \"ema_slow\": 97824.13590241827, \"volume_ratio\": 0.0002137801496817349, \"current_price\": 94666.7}}'),
(141, 'BTCUSDT', 'SELL', 0.525, 94666.7, '2025-06-20 13:53:06', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 101978.99120318258, \"market_data\": {\"volatility\": 1.1291649232183454, \"volume_24h\": 11789.113, \"price_change_24h\": -8.007521354232464}, \"take_profit\": 83698.26319522611, \"current_price\": 94666.7, \"risk_reward_ratio\": 1.5000000000000009, \"strategy_indicators\": {\"atr\": 3656.1456015912945, \"roc\": -4.129162278214375, \"rsi\": 39.30247849573088, \"ema_fast\": 94958.14595217736, \"ema_slow\": 97824.13590241827, \"volume_ratio\": 0.0002137801496817349, \"current_price\": 94666.7}}'),
(142, 'BTCUSDT', 'SELL', 0.525, 94666.7, '2025-06-20 13:53:09', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 101978.99120318258, \"market_data\": {\"volatility\": 1.1291649232183454, \"volume_24h\": 11789.113, \"price_change_24h\": -8.007521354232464}, \"take_profit\": 83698.26319522611, \"current_price\": 94666.7, \"risk_reward_ratio\": 1.5000000000000009, \"strategy_indicators\": {\"atr\": 3656.1456015912945, \"roc\": -4.129162278214375, \"rsi\": 39.30247849573088, \"ema_fast\": 94958.14595217736, \"ema_slow\": 97824.13590241827, \"volume_ratio\": 0.0002137801496817349, \"current_price\": 94666.7}}'),
(143, 'BTCUSDT', 'SELL', 0.525, 94666.7, '2025-06-20 13:53:13', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 101978.99120318258, \"market_data\": {\"volatility\": 1.1291649232183454, \"volume_24h\": 11789.113, \"price_change_24h\": -8.007521354232464}, \"take_profit\": 83698.26319522611, \"current_price\": 94666.7, \"risk_reward_ratio\": 1.5000000000000009, \"strategy_indicators\": {\"atr\": 3656.1456015912945, \"roc\": -4.129162278214375, \"rsi\": 39.30247849573088, \"ema_fast\": 94958.14595217736, \"ema_slow\": 97824.13590241827, \"volume_ratio\": 0.0002137801496817349, \"current_price\": 94666.7}}'),
(144, 'BTCUSDT', 'SELL', 0.525, 94666.7, '2025-06-20 13:53:17', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 101978.99120318258, \"market_data\": {\"volatility\": 1.1291649232183454, \"volume_24h\": 11789.113, \"price_change_24h\": -8.007521354232464}, \"take_profit\": 83698.26319522611, \"current_price\": 94666.7, \"risk_reward_ratio\": 1.5000000000000009, \"strategy_indicators\": {\"atr\": 3656.1456015912945, \"roc\": -4.129162278214375, \"rsi\": 39.30247849573088, \"ema_fast\": 94958.14595217736, \"ema_slow\": 97824.13590241827, \"volume_ratio\": 0.0002137801496817349, \"current_price\": 94666.7}}'),
(145, 'BTCUSDT', 'SELL', 0.525, 94666.7, '2025-06-20 13:53:20', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 101978.99120318258, \"market_data\": {\"volatility\": 1.1291649232183454, \"volume_24h\": 11789.113, \"price_change_24h\": -8.007521354232464}, \"take_profit\": 83698.26319522611, \"current_price\": 94666.7, \"risk_reward_ratio\": 1.5000000000000009, \"strategy_indicators\": {\"atr\": 3656.1456015912945, \"roc\": -4.129162278214375, \"rsi\": 39.30247849573088, \"ema_fast\": 94958.14595217736, \"ema_slow\": 97824.13590241827, \"volume_ratio\": 0.0002137801496817349, \"current_price\": 94666.7}}'),
(146, 'BTCUSDT', 'SELL', 0.525, 94666.7, '2025-06-20 13:53:25', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 101978.99120318258, \"market_data\": {\"volatility\": 1.1291649232183454, \"volume_24h\": 11789.113, \"price_change_24h\": -8.007521354232464}, \"take_profit\": 83698.26319522611, \"current_price\": 94666.7, \"risk_reward_ratio\": 1.5000000000000009, \"strategy_indicators\": {\"atr\": 3656.1456015912945, \"roc\": -4.129162278214375, \"rsi\": 39.30247849573088, \"ema_fast\": 94958.14595217736, \"ema_slow\": 97824.13590241827, \"volume_ratio\": 0.0002137801496817349, \"current_price\": 94666.7}}'),
(147, 'BTCUSDT', 'SELL', 0.525, 94878.1, '2025-06-20 13:53:31', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 102190.3912031826, \"market_data\": {\"volatility\": 1.1293113564457078, \"volume_24h\": 11789.174, \"price_change_24h\": -7.802093152069338}, \"take_profit\": 83909.66319522612, \"current_price\": 94878.1, \"risk_reward_ratio\": 1.5000000000000009, \"strategy_indicators\": {\"atr\": 3656.1456015912945, \"roc\": -3.915073320910631, \"rsi\": 39.90085755484824, \"ema_fast\": 95000.42595217738, \"ema_slow\": 97843.35408423646, \"volume_ratio\": 0.00031727524696569497, \"current_price\": 94878.1}}'),
(148, 'BTCUSDT', 'SELL', 0.525, 94878.1, '2025-06-20 13:53:39', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 102190.3912031826, \"market_data\": {\"volatility\": 1.1293113564457078, \"volume_24h\": 11789.174, \"price_change_24h\": -7.802093152069338}, \"take_profit\": 83909.66319522612, \"current_price\": 94878.1, \"risk_reward_ratio\": 1.5000000000000009, \"strategy_indicators\": {\"atr\": 3656.1456015912945, \"roc\": -3.915073320910631, \"rsi\": 39.90085755484824, \"ema_fast\": 95000.42595217738, \"ema_slow\": 97843.35408423646, \"volume_ratio\": 0.00031727524696569497, \"current_price\": 94878.1}}'),
(149, 'BTCUSDT', 'SELL', 0.525, 94878.1, '2025-06-20 13:53:44', 0, NULL, NULL, 'momentum', 'Momentum BEARISH: EMA медвежий, RSI слабый, ROC падает', NULL, NULL, '{\"stop_loss\": 102190.3912031826, \"market_data\": {\"volatility\": 1.1293113564457078, \"volume_24h\": 11789.174, \"price_change_24h\": -7.802093152069338}, \"take_profit\": 83909.66319522612, \"current_price\": 94878.1, \"risk_reward_ratio\": 1.5000000000000009, \"strategy_indicators\": {\"atr\": 3656.1456015912945, \"roc\": -3.915073320910631, \"rsi\": 39.90085755484824, \"ema_fast\": 95000.42595217738, \"ema_slow\": 97843.35408423646, \"volume_ratio\": 0.00031727524696569497, \"current_price\": 94878.1}}');

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
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `entry_price` float DEFAULT NULL COMMENT 'Цена входа (дубликат price для ясности)',
  `exit_price` float DEFAULT NULL COMMENT 'Цена выхода (дубликат close_price)',
  `risk_reward_ratio` float DEFAULT NULL COMMENT 'Соотношение риск/прибыль'
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

--
-- Дамп данных таблицы `trading_logs`
--

INSERT INTO `trading_logs` (`id`, `log_level`, `category`, `message`, `context`, `symbol`, `strategy`, `trade_id`, `signal_id`, `created_at`) VALUES
(1, 'INFO', 'social', 'Twitter клиент инициализирован', '{}', NULL, NULL, NULL, NULL, '2025-06-21 10:00:53'),
(2, 'INFO', 'social', 'Reddit клиент инициализирован', '{}', NULL, NULL, NULL, NULL, '2025-06-21 10:00:53');

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
  `status` varchar(20) DEFAULT 'TRADING',
  `position_size_percent` float DEFAULT '10',
  `risk_level` varchar(20) DEFAULT 'medium',
  `last_strategy_update` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `volume_24h` float DEFAULT NULL COMMENT '24-часовой объем торгов',
  `price_change_24h` float DEFAULT NULL COMMENT 'Изменение цены за 24 часа (%)',
  `last_price` float DEFAULT NULL COMMENT 'Последняя цена',
  `volatility` float DEFAULT NULL COMMENT 'Волатильность'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Дамп данных таблицы `trading_pairs`
--

INSERT INTO `trading_pairs` (`id`, `symbol`, `base_asset`, `quote_asset`, `is_active`, `min_position_size`, `max_position_size`, `strategy`, `created_at`, `stop_loss_percent`, `take_profit_percent`, `updated_at`, `min_order_size`, `max_order_size`, `price_precision`, `quantity_precision`, `status`, `position_size_percent`, `risk_level`, `last_strategy_update`, `volume_24h`, `price_change_24h`, `last_price`, `volatility`) VALUES
(1, 'BTCUSDT', 'BTC', 'USDT', 1, NULL, NULL, 'momentum', '2025-06-13 11:13:12', 1, 3, '2025-06-20 07:54:28', NULL, NULL, NULL, NULL, 'TRADING', 10, 'medium', '2025-06-20 07:54:28', NULL, NULL, NULL, NULL),
(2, 'ETHUSDT', 'ETH', 'USDT', 1, NULL, NULL, 'momentum', '2025-06-13 11:13:12', 1, 3, '2025-06-20 07:54:32', NULL, NULL, NULL, NULL, 'TRADING', 10, 'medium', '2025-06-20 07:54:32', NULL, NULL, NULL, NULL),
(3, 'BNBUSDT', 'BNB', 'USDT', 0, NULL, NULL, 'safe_multi_indicator', '2025-06-13 11:13:12', 1.5, 3, '2025-06-20 06:07:58', NULL, NULL, NULL, NULL, 'TRADING', 10, 'medium', '2025-06-20 09:55:49', NULL, NULL, NULL, NULL),
(4, 'SOLUSDT', 'SOL', 'USDT', 0, NULL, NULL, 'safe_multi_indicator', '2025-06-13 11:13:12', 1.5, 3, '2025-06-20 06:07:58', NULL, NULL, NULL, NULL, 'TRADING', 10, 'medium', '2025-06-20 09:55:49', NULL, NULL, NULL, NULL),
(5, 'ADAUSDT', 'ADA', 'USDT', 0, NULL, NULL, 'safe_multi_indicator', '2025-06-13 10:07:12', 1.5, 3, '2025-06-20 06:07:58', NULL, NULL, NULL, NULL, 'TRADING', 10, 'medium', '2025-06-20 09:55:49', NULL, NULL, NULL, NULL),
(6, 'DOGEUSDT', 'DOGE', 'USDT', 0, NULL, NULL, 'safe_multi_indicator', '2025-06-13 10:07:12', 1.5, 3, '2025-06-20 06:07:58', NULL, NULL, NULL, NULL, 'TRADING', 10, 'medium', '2025-06-20 09:55:49', NULL, NULL, NULL, NULL),
(7, 'XRPUSDT', 'XRP', 'USDT', 0, NULL, NULL, 'safe_multi_indicator', '2025-06-13 10:07:12', 1.5, 3, '2025-06-20 06:07:58', NULL, NULL, NULL, NULL, 'TRADING', 10, 'medium', '2025-06-20 09:55:49', NULL, NULL, NULL, NULL),
(8, 'DOTUSDT', 'DOT', 'USDT', 0, NULL, NULL, 'safe_multi_indicator', '2025-06-13 10:07:12', 1.5, 3, '2025-06-20 06:07:58', NULL, NULL, NULL, NULL, 'TRADING', 10, 'medium', '2025-06-20 09:55:49', NULL, NULL, NULL, NULL);

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
  ADD KEY `idx_executed` (`is_executed`),
  ADD KEY `idx_strategy` (`strategy`),
  ADD KEY `idx_signals_symbol_created` (`symbol`,`created_at`),
  ADD KEY `idx_signals_strategy_action` (`strategy`,`action`),
  ADD KEY `idx_signals_executed_created` (`is_executed`,`created_at`);

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
  ADD KEY `signal_id` (`signal_id`),
  ADD KEY `idx_trades_symbol_status` (`symbol`,`status`),
  ADD KEY `idx_trades_strategy_created` (`strategy`,`created_at`);

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
  ADD KEY `idx_symbol` (`symbol`),
  ADD KEY `idx_trading_pairs_active_strategy` (`is_active`,`strategy`);

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
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=150;

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
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

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
