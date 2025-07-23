	/* USER CODE BEGIN Header */
	/**
	  ******************************************************************************
	  * @file           : main.c
	  * @brief          : Main program body
	  ******************************************************************************
	  */
	/* USER CODE END Header */

	#include "main.h"
	#include <string.h>

	UART_HandleTypeDef huart2;
	UART_HandleTypeDef huart3;

	/* USER CODE BEGIN PV */
	uint8_t redData[8];
	uint8_t greenData[8];
	uint8_t rxBuffer[8];
	uint8_t ackBuf[1];


	uint8_t ACK = 0xAC;
	uint8_t waiting_for_ack = 1;
	uint8_t current_state = 1; // 1=RED, 2=RED_WAIT, 3=GREEN, 4=GREEN_WAIT

	uint32_t last_send_time = 0;
	uint32_t action_start_time = 0;

	const uint32_t resend_interval = 5; // ms
	/* USER CODE END PV */

	/* USER CODE BEGIN PFP */
	void SystemClock_Config(void);
	static void MX_GPIO_Init(void);
	static void MX_USART2_UART_Init(void);
	static void MX_USART3_UART_Init(void);
	uint16_t ModRTw_CRC(uint8_t *buf, int len);
	/* USER CODE END PFP */

	int main(void)
	{
	  /* USER CODE BEGIN 1 */
	  HAL_Init();
	  SystemClock_Config();
	  MX_GPIO_Init();
	  MX_USART2_UART_Init();
	  MX_USART3_UART_Init();

	  redData[0] = 0x01; redData[1] = 0x02; redData[2] = 0x03;
	  redData[3] = 0x04; redData[4] = 0x05; redData[5] = 0x06;
	  uint16_t crc_red = ModRTw_CRC(redData, 6);
	  redData[6] = crc_red & 0xFF;
	  redData[7] = (crc_red >> 8) & 0xFF;

	  greenData[0] = 0x06; greenData[1] = 0x05; greenData[2] = 0x04;
	  greenData[3] = 0x03; greenData[4] = 0x02; greenData[5] = 0x01;
	  uint16_t crc_green = ModRTw_CRC(greenData, 6);
	  greenData[6] = crc_green & 0xFF;
	  greenData[7] = (crc_green >> 8) & 0xFF;


	  /* USER CODE END 1 */

	  /* USER CODE BEGIN 2 */
	  while (1)
	  {
			HAL_UART_Receive_IT(&huart2, ackBuf, 1);

		uint32_t now = HAL_GetTick();
		switch (current_state)
		{
			case 1:
				if (!waiting_for_ack)
				{
					HAL_GPIO_WritePin(GPIOD, GPIO_PIN_14, GPIO_PIN_SET);
					current_state = 2;
					action_start_time = now;
				}
				else if (now - last_send_time >= resend_interval)
				{
					HAL_UART_Transmit(&huart2, redData, 8, 10);
						HAL_UART_Receive_IT(&huart2, ackBuf, 1);


					last_send_time = now;
				}
				break;

			case 2:
				if (now - action_start_time >= 10000)
				{
					HAL_GPIO_WritePin(GPIOD, GPIO_PIN_14, GPIO_PIN_RESET);
					waiting_for_ack = 1;
					current_state = 3;
					last_send_time = 0;
				}
				break;

			case 3:
				if (!waiting_for_ack)
				{
					HAL_GPIO_WritePin(GPIOD, GPIO_PIN_12, GPIO_PIN_SET);
					current_state = 4;
					action_start_time = now;
				}
				else if (now - last_send_time >= resend_interval)
				{
					HAL_UART_Transmit(&huart2, greenData, 8, 10);
					HAL_UART_Receive_IT(&huart2, ackBuf, 1);
					last_send_time = now;
				}
				break;

			case 4:
				if (now - action_start_time >= 6000)
				{
					HAL_GPIO_WritePin(GPIOD, GPIO_PIN_12, GPIO_PIN_RESET);
					waiting_for_ack = 1;
					current_state = 1;
					last_send_time = 0;
				}
				break;
		}
	  }
	  /* USER CODE END 2 */
	}

	/* USER CODE BEGIN 4 */
	uint16_t ModRTw_CRC(uint8_t *buf, int len)
	{
		uint16_t crc = 0xFFFF;
		for (int pos = 0; pos < len; pos++) {
			crc ^= (uint16_t)buf[pos];
			for (int i = 0; i < 8; i++) {
				if ((crc & 0x0001) != 0) {
					crc >>= 1;
					crc ^= 0xA001;
				} else {
					crc >>= 1;
				}
			}
		}
		return crc;
	}

	void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
	{
		if (huart->Instance == USART2)
		{
	if(ACK==ackBuf[0]){
			waiting_for_ack = 0;
	}


	if(ackBuf[0]==0x00){
		HAL_GPIO_WritePin(GPIOD, GPIO_PIN_12, GPIO_PIN_RESET);
		HAL_GPIO_WritePin(GPIOD, GPIO_PIN_14, GPIO_PIN_RESET);
		waiting_for_ack=0;
		current_state=1;
		HAL_UART_Transmit_IT(&huart2, redData,8);
	}
	if(ackBuf[0]==0x01)
	{
		HAL_GPIO_WritePin(GPIOD, GPIO_PIN_12, GPIO_PIN_RESET);
				HAL_GPIO_WritePin(GPIOD, GPIO_PIN_14, GPIO_PIN_RESET);
		waiting_for_ack=0;
		current_state=3;
		HAL_UART_Transmit_IT(&huart2, greenData, 8);
	}
		}

	}

	void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin)
	{
	  if (GPIO_Pin == GPIO_PIN_0)
	  {
		HAL_GPIO_WritePin(GPIOD, GPIO_PIN_12 | GPIO_PIN_14, GPIO_PIN_RESET);
		current_state = 1;
		waiting_for_ack = 1;
		last_send_time = 0;
	  }
	}

	void SystemClock_Config(void)
	{
	  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
	  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

	  __HAL_RCC_PWR_CLK_ENABLE();
	  __HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE1);

	  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE;
	  RCC_OscInitStruct.HSEState = RCC_HSE_ON;
	  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
	  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
	  RCC_OscInitStruct.PLL.PLLM = 4;
	  RCC_OscInitStruct.PLL.PLLN = 50;
	  RCC_OscInitStruct.PLL.PLLP = RCC_PLLP_DIV2;
	  RCC_OscInitStruct.PLL.PLLQ = 4;
	  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK) Error_Handler();

	  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK|
									RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
	  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
	  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
	  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2;
	  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

	  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_1) != HAL_OK) Error_Handler();
	}

	static void MX_GPIO_Init(void)
	{
	  __HAL_RCC_GPIOD_CLK_ENABLE();
	  __HAL_RCC_GPIOA_CLK_ENABLE();

	  GPIO_InitTypeDef GPIO_InitStruct = {0};

	  GPIO_InitStruct.Pin = GPIO_PIN_12 | GPIO_PIN_14;
	  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
	  GPIO_InitStruct.Pull = GPIO_NOPULL;
	  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
	  HAL_GPIO_Init(GPIOD, &GPIO_InitStruct);

	  GPIO_InitStruct.Pin = GPIO_PIN_0;
	  GPIO_InitStruct.Mode = GPIO_MODE_IT_RISING;
	  GPIO_InitStruct.Pull = GPIO_NOPULL;
	  HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

	  HAL_NVIC_SetPriority(EXTI0_IRQn, 0, 0);
	  HAL_NVIC_EnableIRQ(EXTI0_IRQn);
	}

	static void MX_USART2_UART_Init(void)
	{
	  huart2.Instance = USART2;
	  huart2.Init.BaudRate = 115200;
	  huart2.Init.WordLength = UART_WORDLENGTH_8B;
	  huart2.Init.StopBits = UART_STOPBITS_1;
	  huart2.Init.Parity = UART_PARITY_NONE;
	  huart2.Init.Mode = UART_MODE_TX_RX;
	  huart2.Init.HwFlowCtl = UART_HWCONTROL_NONE;
	  huart2.Init.OverSampling = UART_OVERSAMPLING_16;
	  if (HAL_UART_Init(&huart2) != HAL_OK) Error_Handler();
	}

	static void MX_USART3_UART_Init(void)
	{
	  huart3.Instance = USART3;
	  huart3.Init.BaudRate = 115200;
	  huart3.Init.WordLength = UART_WORDLENGTH_8B;
	  huart3.Init.StopBits = UART_STOPBITS_1;
	  huart3.Init.Parity = UART_PARITY_NONE;
	  huart3.Init.Mode = UART_MODE_TX_RX;
	  huart3.Init.HwFlowCtl = UART_HWCONTROL_NONE;
	  huart3.Init.OverSampling = UART_OVERSAMPLING_16;
	  if (HAL_UART_Init(&huart3) != HAL_OK) Error_Handler();
	}

	void Error_Handler(void)
	{
	  __disable_irq();
	  while (1) {}
	}

	#ifdef USE_FULL_ASSERT
	void assert_failed(uint8_t *file, uint32_t line)
	{
	  // printf("Wrong parameters value: file %s on line %ld\r\n", file, line);
	}
	#endif
