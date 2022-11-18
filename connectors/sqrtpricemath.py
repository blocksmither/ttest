# Source: https://docs.uniswap.org/protocol/reference/core/libraries/SqrtPriceMath
# Source: https://github.com/Uniswap/v3-sdk/blob/main/src/utils/sqrtPriceMath.ts

MaxUint160 = 2 ** 160 - 1
MaxUint256 = 115792089237316195423570985008687907853269984665640564039457584007913129639935
Q96 = 2 ** 96


def invariant(text, value):
    if not value:
        raise Exception(f"invariant: {text}")


def mulDivRoundingUp(a, b, denominator):
    product = a * b
    result = product // denominator
    if product % denominator != 0:
        result = result + 1
    return result


def multiplyIn256(x, y):
    product = x * y
    return product & MaxUint256


def addIn256(x, y):
    sum = x + y
    return sum & MaxUint256


class SqrtPriceMath:
    @staticmethod
    def getNextSqrtPriceFromAmount0RoundingUp(sqrtPX96, liquidity, amount, add):
        """
        Gets the next sqrt price given a delta of token0

        Always rounds up, because in the exact output case (increasing price) we
        need to move the price at least far enough to get the desired output amount,
        and in the exact input case (decreasing price) we need to move the price
        less in order to not send too much output. The most precise formula for this
        is liquidity sqrtPX96 / (liquidity +- amount sqrtPX96), if this is
        impossible because of overflow, we calculate
        liquidity / (liquidity / sqrtPX96 +- amount).

        Parameters:
        Name      -- Type -- Description
        sqrtPX96  -- int  -- The starting price, i.e. before accounting for the token0 delta
        liquidity -- int  -- The amount of usable liquidity
        amount    -- int  -- How much of token0 to add or remove from virtual reserves
        add       -- bool -- Whether to add or remove the amount of token0
        Return Values:
        Type    -- Description
        int -- price after adding or removing amount, depending on add
        """
        if sqrtPX96 == 0:
            return sqrtPX96
        numerator1 = liquidity << 96

        if add:
            product = multiplyIn256(amount, sqrtPX96)
            if product // amount == sqrtPX96:
                denominator = addIn256(numerator1, product)
                if denominator >= numerator1:
                    return mulDivRoundingUp(numerator1, sqrtPX96, denominator)
            return mulDivRoundingUp(numerator1, 1, (numerator1 // sqrtPX96) + amount)
        else:
            product = multiplyIn256(amount, sqrtPX96)

            invariant('(product / amount) == sqrtPX96', (product // amount) == sqrtPX96)
            invariant('numerator1 > product', numerator1 > product)

            denominator = numerator1 - product
            return mulDivRoundingUp(numerator1, sqrtPX96, denominator)

    @staticmethod
    def getNextSqrtPriceFromAmount1RoundingDown(sqrtPX96, liquidity, amount, add):
        """
        Gets the next sqrt price given a delta of token1

        Always rounds down, because in the exact output case (decreasing price)
        we need to move the price at least far enough to get the desired output amount,
        and in the exact input case (increasing price) we need to move the price
        less in order to not send too much output. The formula we compute is
        within <1 wei of the lossless version: sqrtPX96 +- amount / liquidity

        Parameters:
        Name      -- Type -- Description
        sqrtPX96  -- int  -- The starting price, i.e., before accounting for the token1 delta
        liquidity -- int  -- The amount of usable liquidity
        amount    -- int  -- How much of token1 to add, or remove, from virtual reserves
        add       -- bool -- Whether to add, or remove, the amount of token1
        Return Values:
        Type    -- Description
        int -- price after adding or removing amount
        """
        if add:
            if amount <= MaxUint160:
                quotient = (amount << 96) // liquidity
            else:
                quotient = (amount * Q96) // liquidity
            return sqrtPX96 + quotient
        else:
            quotient = mulDivRoundingUp(amount, Q96, liquidity)

            invariant('sqrtPX96 > quotient', sqrtPX96 > quotient)
            return sqrtPX96 - quotient

    @staticmethod
    def getNextSqrtPriceFromInput(sqrtPX96, liquidity, amountIn, zeroForOne):
        """
        Gets the next sqrt price given an input amount of token0 or token1

        Throws if price or liquidity are 0, or if the next price is out of bounds

        Parameters:
        Name       -- Type -- Description
        sqrtPX96   -- int  -- The starting price, i.e., before accounting for the input amount
        liquidity  -- int  -- The amount of usable liquidity
        amountIn   -- int  -- How much of token0, or token1, is being swapped in
        zeroForOne -- bool -- Whether the amount in is token0 or token1
        Return Values:
        Name     -- Type    -- Description
        sqrtQX96 -- int -- The price after adding the input amount to token0 or token1
        """
        invariant('sqrtPX96 > 0', sqrtPX96 > 0)
        invariant('liquidity > 0', liquidity > 0)

        if zeroForOne:
            return SqrtPriceMath.getNextSqrtPriceFromAmount0RoundingUp(sqrtPX96, liquidity, amountIn, True)
        else:
            return SqrtPriceMath.getNextSqrtPriceFromAmount1RoundingDown(sqrtPX96, liquidity, amountIn, True)

    @staticmethod
    def getNextSqrtPriceFromOutput(sqrtPX96, liquidity, amountOut, zeroForOne):
        """
        Gets the next sqrt price given an output amount of token0 or token1

        Throws if price or liquidity are 0 or the next price is out of bounds

        Parameters:
        Name       -- Type -- Description
        sqrtPX96   -- int  -- The starting price before accounting for the output amount
        liquidity  -- int  -- The amount of usable liquidity
        amountOut  -- int  -- How much of token0, or token1, is being swapped out
        zeroForOne -- bool -- Whether the amount out is token0 or token1
        Return Values:
        Name     -- Type    -- Description
        sqrtQX96 -- int -- The price after removing the output amount of token0 or token1
        """
        invariant('sqrtPX96 > 0', sqrtPX96 > 0)
        invariant('liquidity > 0', liquidity > 0)

        if zeroForOne:
            return SqrtPriceMath.getNextSqrtPriceFromAmount1RoundingDown(sqrtPX96, liquidity, amountOut, False)
        else:
            return SqrtPriceMath.getNextSqrtPriceFromAmount0RoundingUp(sqrtPX96, liquidity, amountOut, False)
