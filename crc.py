GEN_POL = '1011'

def xor(a, b):
    result = []
    for i in range(1, len(b)):
        result.append('0' if a[i] == b[i] else '1')
    return ''.join(result)

def crc_division(data):
    n = len(GEN_POL)
    dividend = data + '0'*(n-1)
    temp = dividend[:n]

    for i in range(len(data)):
        if temp[0] == '1':
            temp = xor(temp, GEN_POL) + dividend[n+i:n+i+1]
        else:
            temp = xor(temp, '0'*n) + dividend[n+i:n+i+1]
    
    remainder = temp[:n-1]
    return remainder

def create_packet(message):
    message_ascii = ''.join(format(ord(c), '08b') for c in message)
    remainder = crc_division(message_ascii)
    packet = message + '|' + remainder
    return packet.encode()

def verify_packet(packet):
    try:
        packet_str = packet.decode()
        message, received_crc = packet_str.split('|')
        message_ascii = ''.join(format(ord(c), '08b') for c in message)
        calculated_crc = crc_division(message_ascii)
        
        if calculated_crc == received_crc:
            return True, message
        else:
            return False, None
    except:
        return False, None