-- phpMyAdmin SQL Dump
-- version 5.1.1deb5ubuntu1
-- https://www.phpmyadmin.net/
--
-- Хост: localhost
-- Время создания: Июн 18 2025 г., 17:01
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
  `notes` text,
  `user_id` int DEFAULT NULL COMMENT 'ID пользователя (может быть NULL для старых записей)'
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
  `is_active` tinyint(1) DEFAULT '1',
  `min_position_size` float DEFAULT NULL,
  `max_position_size` float DEFAULT NULL,
  `strategy` varchar(50) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `stop_loss_percent` float DEFAULT '2',
  `take_profit_percent` float DEFAULT '4',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

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
  ADD KEY `idx_closed_at` (`closed_at`),
  ADD KEY `user_id` (`user_id`);

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
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

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
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

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
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT для таблицы `users`
--
ALTER TABLE `users`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- Ограничения внешнего ключа сохраненных таблиц
--

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
  ADD CONSTRAINT `trades_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

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
